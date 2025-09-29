import os
import base64
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText

try:
    from common.supabase_client import get_supabase_client
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from common.supabase_client import get_supabase_client


def _parse_email_timestamp(timestamp_str: str) -> str:
    """Parse email timestamp from various formats to ISO 8601"""
    if not timestamp_str:
        return datetime.now().isoformat()
    
    try:
        # Try parsing RFC 2822 format (Gmail format)
        if '(' in timestamp_str and ')' in timestamp_str:
            # Remove timezone info in parentheses
            clean_timestamp = timestamp_str.split('(')[0].strip()
            dt = datetime.strptime(clean_timestamp, '%a, %d %b %Y %H:%M:%S %z')
            return dt.isoformat()
        
        # Try other common formats
        formats = [
            '%a, %d %b %Y %H:%M:%S %z',  # RFC 2822
            '%Y-%m-%d %H:%M:%S',         # Simple format
            '%Y-%m-%dT%H:%M:%S',         # ISO without timezone
            '%Y-%m-%dT%H:%M:%SZ',        # ISO with Z
            '%Y-%m-%dT%H:%M:%S.%fZ',     # ISO with microseconds
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
                
        # If all parsing fails, return current time
        return datetime.now().isoformat()
        
    except Exception:
        return datetime.now().isoformat()


class GoogleEmailService:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID") 
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    # async def get_emails(self, access_token: str, limit: int = 50, refresh_token: str = None) -> List[Dict[str, Any]]:
    #     print(f"access_tokenaccess_tokenaccess_tokenaccess_tokenaccess_token {access_token}")
    #     print(f"refresh_tokenrefresh_tokenrefresh_tokenrefresh_tokenrefresh_token {refresh_token}") 
    #     print(f"client_idclient_idclient_idclient_idclient_id {os.getenv("GOOGLE_CLIENT_ID")}")
    #     print(f"client_secretclient_secretclient_secretclient_secretclient_secret {os.getenv("GOOGLE_CLIENT_SECRET")}")    
    #     credentials = Credentials(
    #         token=access_token,
    #         refresh_token=refresh_token,
    #         token_uri="https://oauth2.googleapis.com/token",
    #         client_id=os.getenv("GOOGLE_CLIENT_ID"),
    #         client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    #     )

    #     service = build('gmail', 'v1', credentials=credentials)
        
    #     # Get list of messages
    #     results = service.users().messages().list(userId='me', maxResults=limit).execute()
    #     messages = results.get('messages', [])
        
    #     emails = []
    #     for message in messages:
    #         msg = service.users().messages().get(userId='me', id=message['id']).execute()
            
    #         # Extract headers
    #         headers = msg['payload'].get('headers', [])
    #         subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
    #         sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
    #         recipient = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown Recipient')
    #         date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
    #         # Extract body
    #         body = self._extract_body(msg['payload'])
            
    #         emails.append({
    #             'id': message['id'],
    #             'subject': subject,
    #             'sender': sender,
    #             'recipient': recipient,
    #             'body': body,
    #             'timestamp': _parse_email_timestamp(date),
    #             'is_read': 'UNREAD' not in msg['labelIds']
    #         })
        
    #     return emails
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from Gmail API payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    async def send_email(self, access_token: str, to_emails: List[str], subject: str, body: str, is_html: bool = False, refresh_token: str = None) -> str:
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        service = build('gmail', 'v1', credentials=credentials)
        
        # Create message
        message = MIMEText(body, 'html' if is_html else 'plain')
        message['to'] = ', '.join(to_emails)
        message['subject'] = subject
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send message
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return result['id']


class OutlookEmailService:
    def __init__(self):
        pass
    
    # async def get_emails(self, access_token: str, limit: int = 50) -> List[Dict[str, Any]]:
    #     headers = {
    #         'Authorization': f'Bearer {access_token}',
    #         'Content-Type': 'application/json'
    #     }
        
    #     url = f"https://graph.microsoft.com/v1.0/me/messages?$top={limit}&$orderby=receivedDateTime desc"
        
    #     async with httpx.AsyncClient() as client:
    #         response = await client.get(url, headers=headers)
    #         response.raise_for_status()
    #         data = response.json()
        
    #     emails = []
    #     for message in data.get('value', []):
    #         emails.append({
    #             'id': message['id'],
    #             'subject': message.get('subject', 'No Subject'),
    #             'sender': message['from']['emailAddress']['address'],
    #             'recipient': message['toRecipients'][0]['emailAddress']['address'] if message.get('toRecipients') else '',
    #             'body': message.get('body', {}).get('content', ''),
    #             'timestamp': message['receivedDateTime'],
    #             'is_read': message.get('isRead', False)
    #         })
        
    #     return emails
    
    async def send_email(self, access_token: str, to_emails: List[str], subject: str, body: str, is_html: bool = False) -> str:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML" if is_html else "Text",
                    "content": body
                },
                "toRecipients": [
                    {"emailAddress": {"address": email}} for email in to_emails
                ]
            }
        }
        
        url = "https://graph.microsoft.com/v1.0/me/sendMail"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=message)
            response.raise_for_status()
        
        return "sent"  # Microsoft Graph doesn't return a message ID for sendMail


class EmailService:
    def __init__(self):
        self.services = {
            'google': GoogleEmailService(),
            'outlook': OutlookEmailService()
        }
        self.admin = get_supabase_client().get_admin_client()
        self.email_schema_name = 'email'
        self.email_provider_schema_name = 'email_provider'
        self.email_message_name = 'email_message'
        self.email_account_name = 'email_accounts'
        self.lead_name = 'email_lead'
    
    def _normalize_user_id(self, user_id) -> str:
        try:
            if isinstance(user_id, dict) and 'id' in user_id:
                return str(user_id['id'])
            if hasattr(user_id, 'id'):
                return str(user_id.id)
            return str(user_id)
        except Exception:
            return str(user_id)
    
    async def get_user_email_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        result = self.admin.schema(self.email_provider_schema_name).from_(self.email_account_name).select('*').eq('user_id', user_id).execute()
        return result.data
    
    async def _refresh_and_save_tokens(self, account_id: str, provider_name: str, credentials) -> Dict[str, str]:
        """Refresh tokens and save to database"""
        try:
            # Refresh the credentials
            print(f"credentialscredentialscredentialscredentialscredentials {credentials}")
            credentials.refresh(Request())
            print(f"access_tokenaccess_tokenaccess_tokenaccess_tokenaccess_token {credentials.token}")
            print(f"refresh_tokenrefresh_tokenrefresh_tokenrefresh_tokenrefresh_token {credentials.refresh_token}")
            # Update the account with new tokens
            update_data = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            self.admin.schema(self.email_provider_schema_name).from_(self.email_account_name).update(update_data).eq('id', account_id).execute()
            print(f"Refreshed tokens for account {account_id}")
            
            return {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token
            }
        except Exception as e:
            print(f"Failed to refresh tokens: {e}")
            raise ValueError(f"Token refresh failed: {e}")
    
    async def _get_credentials_with_refresh(self, account: Dict[str, Any]) -> Any:
        """Get credentials with automatic refresh capability"""
        if account['provider'] == 'google':
            credentials = Credentials(
                token=account['access_token'],
                refresh_token=account.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("GOOGLE_CLIENT_ID"),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
            )
            # Check if token is expired and refresh if needed
            if not credentials.valid:
                if credentials.expired and credentials.refresh_token:
                    print(f"Token expired for account {account['id']}, refreshing...")
                    await self._refresh_and_save_tokens(account['id'], account['provider'], credentials)
                else:
                    raise ValueError("Token expired and no refresh token available")
            
            return credentials
        else:
            # For other providers, return the access token as-is
            return None

    async def get_emails(self, user_id: str, lead_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        # Get account details
        account_result = self.admin.schema(self.email_provider_schema_name).from_(self.email_account_name).select('*').eq('user_id', user_id).execute()
        print(f"account_resultaccount_resultaccount_resultaccount_resultaccount_result {account_result}")
        if not account_result.data:
            raise ValueError("Account not found")
        
        account = account_result.data[0]
        # Get emails from provider
        if account['provider'] not in self.services:
            raise ValueError(f"Unsupported provider: {account['provider']}")
        
        email_result = self.admin.schema(self.email_schema_name).from_(self.email_message_name).select('*').eq('user_id', user_id).eq('lead_id', lead_id).limit(limit).execute()
        emails = email_result.data
        # Store emails in database
        result = []
        for email in emails:
            email_data = {
                'user_id': user_id,
                'lead_id': email['lead_id'],
                'message_id': email['message_id'],
                'subject': email['subject'],
                'sender': email['sender'],
                'receiver': email['receiver'],
                'body': email['body'],
                'summary': email['summary'],
                'internal_date': email['internal_date'],
                'is_read': email['is_read']
            }
            result.append(email_data)
            
        return result

    async def get_leads(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        lead_result = self.admin.schema(self.email_schema_name).from_(self.lead_name).select('*').eq('user_id', user_id).limit(limit).execute()
        leads = lead_result.data
        result = [] 
        for lead in leads:
            lead_data = {
                'id': lead['lead_id'],
                'owner': lead['owner'],
                'subject': lead['subject'],
                'internal_date': lead['internal_date']
            }
            result.append(lead_data)
        return result
    
    async def send_email(self, user_id: str, account_id: str, to_emails: List[str], subject: str, body: str, is_html: bool = False) -> str:
        # Get account details
        account_result = self.admin.schema(self.email_provider_schema_name).from_(self.email_account_name).select('*').eq('id', account_id).eq('user_id', user_id).execute()
        
        if not account_result.data:
            raise ValueError("Account not found")
        
        account = account_result.data[0]
        new_credentials = await self._get_credentials_with_refresh(account)
        
        if new_credentials:
            account['access_token'] = new_credentials.token
            account['refresh_token'] = new_credentials.refresh_token
        
        # Send email via provider
        if account['provider'] not in self.services:
            raise ValueError(f"Unsupported provider: {account['provider']}")
        
        service = self.services[account['provider']]
        message_id = await service.send_email(
            account['access_token'],
            to_emails,
            subject,
            body,
            is_html,
            account.get('refresh_token')
        )
        
        return message_id
    
    async def save_draft(self, user_id: str, account_id: str, to_emails: List[str], subject: str, body: str, is_html: bool = False) -> Dict[str, Any]:
        """Save email as draft"""
        draft_data = {
            'user_id': user_id,
            'account_id': account_id,
            'to': to_emails,
            'subject': subject,
            'body': body,
            'is_html': is_html,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = self.admin.schema('email').from_('draft_emails').insert(draft_data).execute()
        return result.data[0]
    
    async def get_drafts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all draft emails for the user"""
        result = self.admin.schema('email').from_('draft_emails').select('*').eq('user_id', user_id).order('updated_at', desc=True).execute()
        return result.data
    
    async def get_draft(self, user_id: str, draft_id: str) -> Dict[str, Any]:
        """Get a specific draft email"""
        result = self.admin.schema('email').from_('draft_emails').select('*').eq('id', draft_id).eq('user_id', user_id).execute()
        
        if not result.data:
            raise ValueError("Draft not found")
        
        return result.data[0]
    
    async def update_draft(self, user_id: str, draft_id: str, to_emails: List[str], subject: str, body: str, is_html: bool = False) -> Dict[str, Any]:
        """Update a draft email"""
        # Check if draft exists and belongs to user
        existing = self.admin.schema('email').from_('draft_emails').select('*').eq('id', draft_id).eq('user_id', user_id).execute()
        if not existing.data:
            raise ValueError("Draft not found")
        
        # Update draft data
        update_data = {
            'to': to_emails,
            'subject': subject,
            'body': body,
            'is_html': is_html,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = self.admin.schema('email').from_('draft_emails').update(update_data).eq('id', draft_id).eq('user_id', user_id).execute()
        return result.data[0]
    
    async def delete_draft(self, user_id: str, draft_id: str) -> bool:
        """Delete a draft email"""
        # Check if draft exists and belongs to user
        existing = self.admin.schema('email').from_('draft_emails').select('*').eq('id', draft_id).eq('user_id', user_id).execute()
        if not existing.data:
            raise ValueError("Draft not found")
        
        # Delete draft
        self.admin.schema('email').from_('draft_emails').delete().eq('id', draft_id).eq('user_id', user_id).execute()
        return True
    
    async def send_draft(self, user_id: str, draft_id: str, account_id: str) -> str:
        """Send a draft email"""
        # Get draft
        draft_result = self.admin.schema('email').from_('draft_emails').select('*').eq('id', draft_id).eq('user_id', user_id).execute()
        if not draft_result.data:
            raise ValueError("Draft not found")
        
        draft = draft_result.data[0]
        
        # Send email
        result = await self.send_email(
            user_id=user_id,
            account_id=account_id,
            to_emails=draft['to'],
            subject=draft['subject'],
            body=draft['body'],
            is_html=draft['is_html']
        )
        
        # Delete draft after sending
        self.admin.schema('email').from_('draft_emails').delete().eq('id', draft_id).eq('user_id', user_id).execute()
        
        return result