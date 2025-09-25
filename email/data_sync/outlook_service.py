"""
Outlook API service for reading and syncing emails.
Handles Microsoft Graph API authentication and email data extraction.
"""

import logging
import json
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import EmailMessageCreate, EmailAccount

logger = logging.getLogger(__name__)

# Microsoft Graph API endpoints
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPES = [
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/Mail.ReadWrite"
]


class OutlookService:
    """Service for interacting with Microsoft Graph API (Outlook)."""
    
    def __init__(self):
        """Initialize Outlook service."""
        self.access_token = None
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def authenticate_with_token(self, access_token: str) -> bool:
        """Authenticate using access token."""
        try:
            self.access_token = access_token
            
            # Test the token by making a simple API call
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.get(
                f"{GRAPH_BASE_URL}/me",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Outlook authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Outlook authentication error: {str(e)}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def get_folders(self) -> List[Dict[str, str]]:
        """Get list of Outlook mail folders."""
        try:
            if not self.access_token:
                raise Exception("Outlook service not authenticated")
            
            headers = self._get_headers()
            response = self.session.get(
                f"{GRAPH_BASE_URL}/me/mailFolders",
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            data = response.json()
            folders = []
            
            for folder in data.get('value', []):
                folders.append({
                    'id': folder['id'],
                    'name': folder['displayName'],
                    'type': 'system' if folder.get('isHidden', False) else 'user'
                })
            
            return folders
            
        except Exception as e:
            logger.error(f"Error getting Outlook folders: {str(e)}")
            return []
    
    def get_messages(self, folder_id: str = 'inbox', max_results: int = 100, 
                    query: str = '') -> List[Dict[str, Any]]:
        """Get messages from Outlook."""
        try:
            if not self.access_token:
                raise Exception("Outlook service not authenticated")
            
            headers = self._get_headers()
            
            # Build query parameters
            params = {
                '$top': min(max_results, 1000),  # Graph API limit
                '$select': 'id,subject,from,toRecipients,body,receivedDateTime,isRead,parentFolderId,conversationId,internetMessageId',
                '$orderby': 'receivedDateTime desc'
            }
            
            if query:
                params['$filter'] = f"contains(subject,'{query}') or contains(body/content,'{query}')"
            
            # Get messages
            url = f"{GRAPH_BASE_URL}/me/mailFolders/{folder_id}/messages"
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            data = response.json()
            messages = []
            
            for msg in data.get('value', []):
                try:
                    message_detail = self._process_message(msg)
                    if message_detail:
                        messages.append(message_detail)
                except Exception as e:
                    logger.warning(f"Error processing message {msg.get('id', 'unknown')}: {str(e)}")
                    continue
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting Outlook messages: {str(e)}")
            return []
    
    def _process_message(self, msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single message from Graph API response."""
        try:
            # Extract basic info
            message_id = msg.get('id', '')
            subject = msg.get('subject', '')
            received_date = msg.get('receivedDateTime', '')
            is_read = msg.get('isRead', False)
            parent_folder_id = msg.get('parentFolderId', '')
            conversation_id = msg.get('conversationId', '')
            internet_message_id = msg.get('internetMessageId', '')
            
            # Extract sender
            sender_info = msg.get('from', {})
            sender = sender_info.get('emailAddress', {}).get('address', '') if sender_info else ''
            
            # Extract receiver
            to_recipients = msg.get('toRecipients', [])
            receiver = ', '.join([r.get('emailAddress', {}).get('address', '') for r in to_recipients])
            
            # Extract body
            body_content = msg.get('body', {})
            body = body_content.get('content', '') if body_content else ''
            content_type = body_content.get('contentType', 'text')
            
            # Convert HTML to text if needed
            if content_type == 'html':
                body = self._html_to_text(body)
            
            # Parse date
            internal_date = None
            if received_date:
                try:
                    # Parse ISO format date
                    dt = datetime.fromisoformat(received_date.replace('Z', '+00:00'))
                    internal_date = int(dt.timestamp() * 1000)
                except Exception as e:
                    logger.warning(f"Error parsing date {received_date}: {str(e)}")
                    internal_date = int(datetime.now(timezone.utc).timestamp() * 1000)
            else:
                internal_date = int(datetime.now(timezone.utc).timestamp() * 1000)
            
            # Get folder name
            folder = self._get_folder_name(parent_folder_id)
            
            return {
                'message_id': message_id,
                'subject': subject,
                'sender': sender,
                'receiver': receiver,
                'body': body,
                'is_read': is_read,
                'folder': folder,
                'internal_date': internal_date,
                'raw_data': msg,
                'conversation_id': conversation_id,
                'internet_message_id': internet_message_id,
                'parent_folder_id': parent_folder_id
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return None
    
    def _html_to_text(self, html: str) -> str:
        """Simple HTML to text conversion."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _get_folder_name(self, folder_id: str) -> str:
        """Get folder name from folder ID."""
        # Common Outlook folder mappings
        folder_mappings = {
            'inbox': 'inbox',
            'drafts': 'drafts',
            'sentitems': 'sent',
            'deleteditems': 'deleted',
            'junkemail': 'junk',
            'outbox': 'outbox'
        }
        
        # Try to get folder name from API
        try:
            headers = self._get_headers()
            response = self.session.get(
                f"{GRAPH_BASE_URL}/me/mailFolders/{folder_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('displayName', 'unknown').lower()
        except Exception as e:
            logger.warning(f"Error getting folder name for {folder_id}: {str(e)}")
        
        # Fallback to mapping
        return folder_mappings.get(folder_id.lower(), 'inbox')
    
    def sync_emails_to_database(self, account: EmailAccount, user_id: str, 
                               max_messages: int = 100, folder: Optional[str] = None) -> List[EmailMessageCreate]:
        """Sync Outlook emails to database format."""
        try:
            # Authenticate
            if not self.authenticate_with_token(account.access_token):
                raise Exception("Failed to authenticate with Outlook")
            
            # Get messages
            messages = self.get_messages(
                folder_id=folder or 'inbox',
                max_results=max_messages
            )
            
            # Convert to EmailMessageCreate objects
            email_messages = []
            for msg in messages:
                try:
                    email_msg = EmailMessageCreate(
                        message_id=msg['message_id'],
                        lead_id=None,  # Will be set later if needed
                        owner=account.email,
                        sender=msg['sender'],
                        receiver=msg['receiver'],
                        subject=msg['subject'],
                        body=msg['body'],
                        is_read=msg['is_read'],
                        folder=msg['folder'],
                        raw_data=msg['raw_data'],
                        summary=None,  # Will be generated later
                        internal_date=msg['internal_date'],
                        history_id=msg.get('conversation_id')  # Use conversation_id as history_id
                    )
                    email_messages.append(email_msg)
                    
                except Exception as e:
                    logger.warning(f"Error converting message {msg.get('message_id', 'unknown')}: {str(e)}")
                    continue
            
            return email_messages
            
        except Exception as e:
            logger.error(f"Error syncing Outlook emails: {str(e)}")
            return []
    
    def get_unread_count(self, folder_id: str = 'inbox') -> int:
        """Get count of unread messages in a folder."""
        try:
            if not self.access_token:
                raise Exception("Outlook service not authenticated")
            
            headers = self._get_headers()
            params = {
                '$filter': 'isRead eq false',
                '$count': 'true'
            }
            
            response = self.session.get(
                f"{GRAPH_BASE_URL}/me/mailFolders/{folder_id}/messages",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('@odata.count', 0)
            else:
                logger.error(f"Error getting unread count: {response.status_code} - {response.text}")
                return 0
                
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        try:
            if not self.access_token:
                raise Exception("Outlook service not authenticated")
            
            headers = self._get_headers()
            data = {
                'isRead': True
            }
            
            response = self.session.patch(
                f"{GRAPH_BASE_URL}/me/messages/{message_id}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            return False
    
    def get_message_thread(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a conversation."""
        try:
            if not self.access_token:
                raise Exception("Outlook service not authenticated")
            
            headers = self._get_headers()
            params = {
                '$filter': f"conversationId eq '{conversation_id}'",
                '$orderby': 'receivedDateTime asc'
            }
            
            response = self.session.get(
                f"{GRAPH_BASE_URL}/me/messages",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            data = response.json()
            messages = []
            
            for msg in data.get('value', []):
                message_detail = self._process_message(msg)
                if message_detail:
                    messages.append(message_detail)
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
            return []
    
    def get_message_attachments(self, message_id: str) -> List[Dict[str, Any]]:
        """Get attachments for a message."""
        try:
            if not self.access_token:
                raise Exception("Outlook service not authenticated")
            
            headers = self._get_headers()
            response = self.session.get(
                f"{GRAPH_BASE_URL}/me/messages/{message_id}/attachments",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('value', [])
            else:
                logger.error(f"Error getting attachments: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting attachments: {str(e)}")
            return []
