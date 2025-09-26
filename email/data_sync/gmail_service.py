"""
Gmail API service for reading and syncing emails.
Handles Gmail API authentication and email data extraction.
"""

import logging
import base64
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import os
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import EmailMessageCreate, EmailAccount

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly'
]

load_dotenv()
class GmailService:
    """Service for interacting with Gmail API."""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """Initialize Gmail service."""
        self.credentials_path = credentials_path
        self.service = None
    
    def authenticate_with_tokens(self, access_token: str, refresh_token: Optional[str] = None) -> bool:
        """Authenticate using existing tokens."""
        try:
            creds = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("GOOGLE_CLIENT_ID"),  # Will be set from token
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),  # Will be set from token
                scopes=SCOPES
            )
            
            # Refresh token if needed
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            self.service = build('gmail', 'v1', credentials=creds)
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {str(e)}")
            return False
    
    def get_folders(self) -> List[Dict[str, str]]:
        """Get list of Gmail labels (folders)."""
        try:
            if not self.service:
                raise Exception("Gmail service not authenticated")
            
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            folders = []
            for label in labels:
                folders.append({
                    'id': label['id'],
                    'name': label['name'],
                    'type': 'system' if label['type'] == 'system' else 'user'
                })
            
            return folders
            
        except HttpError as e:
            logger.error(f"Error getting Gmail folders: {str(e)}")
            return []
    
    def get_messages(self, folder_id: str = 'INBOX', max_results: int = 100, 
                    query: str = '', include_spam_trash: bool = False) -> List[Dict[str, Any]]:
        """Get messages from Gmail."""
        try:
            if not self.service:
                raise Exception("Gmail service not authenticated")
            
            # Build query
            gmail_query = query
            if folder_id and folder_id != 'ALL':
                gmail_query = f"in:{folder_id} {query}".strip()
            print(f"gmail_query gmail_query gmail_query {gmail_query}")
            
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                q=gmail_query,
                maxResults=max_results,
                includeSpamTrash=include_spam_trash
            ).execute()
            print(f"results results results {len(results)}")
            messages = results.get('messages', [])
            detailed_messages = []
            
            # Get detailed message data
            for message in messages:
                try:
                    msg_detail = self._get_message_detail(message['id'])
                    if msg_detail:
                        detailed_messages.append(msg_detail)
                except Exception as e:
                    logger.warning(f"Error getting message detail for {message['id']}: {str(e)}")
                    continue
            
            return detailed_messages
            
        except HttpError as e:
            logger.error(f"Error getting Gmail messages: {str(e)}")
            return []
    
    def _get_message_detail(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed message information."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            payload = message['payload']
            headers = payload.get('headers', [])
            
            # Extract headers
            header_dict = {header['name'].lower(): header['value'] for header in headers}
            
            # Extract basic info
            subject = header_dict.get('subject', '')
            sender = header_dict.get('from', '')
            receiver = header_dict.get('to', '')
            date_str = header_dict.get('date', '')
            
            # Parse date
            internal_date = message.get('internalDate')
            if internal_date:
                internal_date = int(internal_date)
            else:
                internal_date = int(datetime.now(timezone.utc).timestamp() * 1000)
            
            # Extract body
            body = self._extract_body(payload)
            
            # Extract folder (label)
            labels = message.get('labelIds', [])
            folder = self._get_primary_folder(labels)
            
            # Check if read
            is_read = 'UNREAD' not in labels
            print(f"message.get('threadId'),message.get('threadId'),message.get('threadId'), {message.get('threadId')}")
            return {
                'message_id': message_id,
                'subject': subject,
                'sender': sender,
                'receiver': receiver,
                'body': body,
                'is_read': is_read,
                'folder': folder,
                'internal_date': internal_date,
                'raw_data': message,
                'labels': labels,
                'lead_id': message.get('threadId'),
                'summary': message.get('snippet'),
                'history_id': message.get('historyId')
            }
            
        except Exception as e:
            logger.error(f"Error getting message detail for {message_id}: {str(e)}")
            return None
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload."""
        body = ""
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                elif part['mimeType'] == 'text/html' and not body:
                    data = part['body'].get('data')
                    if data:
                        html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        # Simple HTML to text conversion
                        body = self._html_to_text(html_body)
        else:
            # Single part message
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif payload['mimeType'] == 'text/html':
                data = payload['body'].get('data')
                if data:
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    body = self._html_to_text(html_body)
        
        return body
    
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
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _get_primary_folder(self, labels: List[str]) -> str:
        """Get primary folder from labels."""
        # Priority order for folder detection
        folder_priority = {
            'INBOX': 'inbox',
            'SENT': 'sent',
            'DRAFT': 'drafts',
            'SPAM': 'spam',
            'TRASH': 'trash',
            'IMPORTANT': 'important',
            'STARRED': 'starred'
        }
        
        for label in labels:
            if label in folder_priority:
                return folder_priority[label]
        
        # Check for user labels
        user_labels = [label for label in labels if not label.startswith('Label_')]
        if user_labels:
            return user_labels[0]
        
        return 'inbox'  # Default
    
    def sync_emails_to_database(self, account: EmailAccount, user_id: str, 
                               max_messages: int = 100, folder: Optional[str] = None) -> List[EmailMessageCreate]:
        """Sync Gmail emails to database format."""
        try:
            # Authenticate
            if not self.authenticate_with_tokens(account.access_token, account.refresh_token):
                raise Exception("Failed to authenticate with Gmail")
            print(f"get_messages get_messages get_messages  folder {folder}, max_messages {max_messages}")
            # Get messages
            messages = self.get_messages(
                folder_id=folder or 'INBOX',
                max_results=max_messages
            )
            # Convert to EmailMessageCreate objects
            email_messages = []
            for msg in messages:
                try:
                    print(f"lead_id lead_id lead_id lead_id lead_id {msg.get('lead_id', '')}")
                    print(f"snippet snippet snippet snippet snippet {msg.get('summary', '')}")
                    email_msg = EmailMessageCreate(
                        message_id=msg['message_id'],
                        lead_id=msg.get('lead_id', ''),  # Will be set later if needed
                        owner=account.email,
                        sender=msg['sender'],
                        receiver=msg['receiver'],
                        subject=msg['subject'],
                        body=msg['body'],
                        is_read=msg['is_read'],
                        folder=msg['folder'],
                        raw_data=msg['raw_data'],
                        summary=msg.get('summary', ''), # Will be generated later
                        internal_date=msg['internal_date'],
                        history_id=msg.get('history_id')
                    )
                    email_messages.append(email_msg)
                    
                except Exception as e:
                    logger.warning(f"Error converting message {msg.get('message_id', 'unknown')}: {str(e)}")
                    continue
            
            return email_messages
            
        except Exception as e:
            logger.error(f"Error syncing Gmail emails: {str(e)}")
            return []
    
    def get_unread_count(self, folder_id: str = 'INBOX') -> int:
        """Get count of unread messages in a folder."""
        try:
            if not self.service:
                raise Exception("Gmail service not authenticated")
            
            results = self.service.users().messages().list(
                userId='me',
                q=f'in:{folder_id} is:unread',
                maxResults=1
            ).execute()
            
            return results.get('resultSizeEstimate', 0)
            
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        try:
            if not self.service:
                raise Exception("Gmail service not authenticated")
            
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            return False
    
    def get_message_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a thread."""
        try:
            if not self.service:
                raise Exception("Gmail service not authenticated")
            
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id,
                format='full'
            ).execute()
            
            messages = []
            for message in thread.get('messages', []):
                msg_detail = self._get_message_detail(message['id'])
                if msg_detail:
                    messages.append(msg_detail)
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting thread {thread_id}: {str(e)}")
            return []
