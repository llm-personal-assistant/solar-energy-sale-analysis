import os
import base64
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from msal import ConfidentialClientApplication
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import smtplib

from supabase_client import get_supabase_client

class GoogleEmailProvider:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth-callback/google")
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/userinfo.email'
        ]
    
    def get_auth_url(self, state: str) -> str:
        print(f"Getting auth URL for Google")
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri
        print(f"Redirect URI: {self.redirect_uri}")
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )
        print(f"Auth URL: {auth_url}")
        return auth_url
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, str]:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token
        }
    
    async def get_emails(self, access_token: str, limit: int = 50) -> List[Dict[str, Any]]:
        credentials = Credentials(token=access_token)
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get list of messages
        results = service.users().messages().list(userId='me', maxResults=limit).execute()
        messages = results.get('messages', [])
        
        emails = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            
            # Extract headers
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            recipient = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown Recipient')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = self._extract_body(msg['payload'])
            
            emails.append({
                'id': message['id'],
                'subject': subject,
                'sender': sender,
                'recipient': recipient,
                'body': body,
                'timestamp': date,
                'is_read': 'UNREAD' not in msg['labelIds']
            })
        
        return emails
    
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
    
    async def send_email(self, access_token: str, to_emails: List[str], subject: str, body: str, is_html: bool = False) -> str:
        credentials = Credentials(token=access_token)
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

class OutlookEmailProvider:
    def __init__(self):
        self.client_id = os.getenv("OUTLOOK_CLIENT_ID")
        self.client_secret = os.getenv("OUTLOOK_CLIENT_SECRET")
        self.redirect_uri = os.getenv("OUTLOOK_REDIRECT_URI", "http://localhost:8000/oauth-callback/outlook")
        self.authority = "https://login.microsoftonline.com/common"
        self.scopes = ["https://graph.microsoft.com/Mail.Read", "https://graph.microsoft.com/Mail.Send"]
    
    def get_auth_url(self, state: str) -> str:
        app = ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        auth_url = app.get_authorization_request_url(
            self.scopes,
            redirect_uri=self.redirect_uri,
            state=state
        )
        return auth_url
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, str]:
        app = ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        result = app.acquire_token_by_authorization_code(
            code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        return {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token", "")
        }
    
    async def get_emails(self, access_token: str, limit: int = 50) -> List[Dict[str, Any]]:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"https://graph.microsoft.com/v1.0/me/messages?$top={limit}&$orderby=receivedDateTime desc"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        emails = []
        for message in data.get('value', []):
            emails.append({
                'id': message['id'],
                'subject': message.get('subject', 'No Subject'),
                'sender': message['from']['emailAddress']['address'],
                'recipient': message['toRecipients'][0]['emailAddress']['address'] if message.get('toRecipients') else '',
                'body': message.get('body', {}).get('content', ''),
                'timestamp': message['receivedDateTime'],
                'is_read': message.get('isRead', False)
            })
        
        return emails
    
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

class YahooEmailProvider:
    def __init__(self):
        self.client_id = os.getenv("YAHOO_CLIENT_ID")
        self.client_secret = os.getenv("YAHOO_CLIENT_SECRET")
        self.redirect_uri = os.getenv("YAHOO_REDIRECT_URI", "http://localhost:8000/oauth-callback/yahoo")
        self.scopes = ["mail-r", "mail-w"]
    
    def get_auth_url(self, state: str) -> str:
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.scopes),
            'state': state
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"https://api.login.yahoo.com/oauth2/request_auth?{query_string}"
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, str]:
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code': code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://api.login.yahoo.com/oauth2/get_token',
                data=data
            )
            response.raise_for_status()
            result = response.json()
        
        return {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token", "")
        }
    
    async def get_emails(self, access_token: str, limit: int = 50) -> List[Dict[str, Any]]:
        # Yahoo Mail API is more complex and requires additional steps
        # This is a simplified implementation
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Note: Yahoo Mail API requires additional setup and may not be available
        # This is a placeholder implementation
        return []
    
    async def send_email(self, access_token: str, to_emails: List[str], subject: str, body: str, is_html: bool = False) -> str:
        # Yahoo Mail API for sending emails is complex and may not be available
        # This is a placeholder implementation
        return "yahoo_send_not_implemented"

class EmailProviderManager:
    def __init__(self):
        self.providers = {
            'google': GoogleEmailProvider(),
            'outlook': OutlookEmailProvider(),
            'yahoo': YahooEmailProvider()
        }
        self.supabase = get_supabase_client().get_client()
    
    async def get_auth_url(self, provider: str, user_id: str) -> str:
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Generate state for OAuth
        state = str(uuid.uuid4())
        print(f"State: {state}")
        
        # Store state in database with user_id
        await self._store_oauth_state(state, provider, user_id)
        print(f"Storing state in database with user_id {user_id}")
        return self.providers[provider].get_auth_url(state)
    
    async def handle_oauth_callback(self, user_id: str, provider: str, code: str) -> Dict[str, Any]:
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Exchange code for tokens
        tokens = await self.providers[provider].exchange_code_for_tokens(code)
        
        # Get user email from provider
        user_email = await self._get_user_email_from_provider(provider, tokens['access_token'])
        
        # Create email account
        return await self.create_email_account(
            user_id=user_id,
            email=user_email,
            provider=provider,
            access_token=tokens['access_token'],
            refresh_token=tokens.get('refresh_token')
        )
    
    async def create_email_account(self, user_id: str, email: str, provider: str, access_token: str, refresh_token: str = None) -> Dict[str, Any]:
        account_data = {
            'user_id': user_id,
            'email': email,
            'provider': provider,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'is_active': True
        }
        
        result = self.supabase.table('email_accounts').insert(account_data).execute()
        return result.data[0]
    
    async def get_user_email_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        result = self.supabase.table('email_accounts').select('*').eq('user_id', user_id).execute()
        return result.data
    
    async def get_emails(self, user_id: str, account_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        # Get account details
        account_result = self.supabase.table('email_accounts').select('*').eq('id', account_id).eq('user_id', user_id).execute()
        
        if not account_result.data:
            raise ValueError("Account not found")
        
        account = account_result.data[0]
        provider = self.providers[account['provider']]
        
        # Get emails from provider
        emails = await provider.get_emails(account['access_token'], limit)
        
        # Store emails in database
        for email in emails:
            email_data = {
                'account_id': account_id,
                'message_id': email['id'],
                'subject': email['subject'],
                'sender': email['sender'],
                'recipient': email['recipient'],
                'body': email['body'],
                'timestamp': email['timestamp'],
                'is_read': email['is_read']
            }
            self.supabase.table('email_messages').upsert(email_data).execute()
        
        return emails
    
    async def send_email(self, user_id: str, account_id: str, to_emails: List[str], subject: str, body: str, is_html: bool = False) -> str:
        # Get account details
        account_result = self.supabase.table('email_accounts').select('*').eq('id', account_id).eq('user_id', user_id).execute()
        
        if not account_result.data:
            raise ValueError("Account not found")
        
        account = account_result.data[0]
        provider = self.providers[account['provider']]
        
        # Send email via provider
        message_id = await provider.send_email(
            account['access_token'],
            to_emails,
            subject,
            body,
            is_html
        )
        
        return message_id
    
    async def _store_oauth_state(self, state: str, provider: str, user_id: str):
        state_data = {
            'id': str(uuid.uuid4()),
            'state': state,
            'provider': provider,
            'user_id': user_id,
            'expires_at': (datetime.now() + timedelta(minutes=10)).isoformat(),
            'created_at': datetime.now().isoformat()
        }
        print(f"Storing state in database: {state_data}")
        try:    
            self.supabase.table('oauth_states').insert(state_data).execute()
            print(f"State stored in database")
        except Exception as e:
            print(f"Error storing state in database: {e}")
    
    async def _get_user_email_from_provider(self, provider: str, access_token: str) -> str:
        if provider == 'google':
            # Use Google API to get user info
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
                )
                response.raise_for_status()
                data = response.json()
                return data['email']
        elif provider == 'outlook':
            # Use Microsoft Graph to get user info
            headers = {'Authorization': f'Bearer {access_token}'}
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me",
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                return data['mail']
        else:
            # For Yahoo, this would need to be implemented based on their API
            return "user@yahoo.com"  # Placeholder
    
    async def validate_and_consume_state(self, state: str, provider: str) -> str:
        """Validate the OAuth state and return the associated user_id. Consume the state on success."""
        # Find matching state
        result = self.supabase.table('oauth_states').select('*').eq('state', state).eq('provider', provider).execute()
        if not result.data:
            raise ValueError("Invalid OAuth state")
        record = result.data[0]
        # Check expiry
        try:
            expires_at = datetime.fromisoformat(record['expires_at'])
        except Exception:
            raise ValueError("Malformed OAuth state expiry")
        if expires_at < datetime.now():
            # Cleanup expired state
            self.supabase.table('oauth_states').delete().eq('id', record['id']).execute()
            raise ValueError("OAuth state has expired")
        user_id = record.get('user_id')
        if not user_id:
            raise ValueError("OAuth state is missing user association")
        # Consume state
        self.supabase.table('oauth_states').delete().eq('id', record['id']).execute()
        return user_id
