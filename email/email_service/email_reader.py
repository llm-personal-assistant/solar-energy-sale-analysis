"""
Email Reader Module

Handles reading emails from various providers with automatic token refresh.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path to import provider modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from provider.email_providers import EmailProviderManager


class EmailReader:
    """Handles reading emails from connected email accounts."""
    
    def __init__(self):
        self.provider_manager = EmailProviderManager()
    
    async def get_emails(
        self, 
        user_id: str, 
        account_id: str, 
        limit: int = 50,
        unread_only: bool = False,
        since_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get emails from a specific account.
        
        Args:
            user_id: User identifier
            account_id: Email account identifier
            limit: Maximum number of emails to retrieve
            unread_only: If True, only return unread emails
            since_date: Only return emails since this date
            
        Returns:
            List of email dictionaries
        """
        try:
            # Get emails from provider
            emails = await self.provider_manager.get_emails(user_id, account_id, limit)
            
            # Apply filters
            if unread_only:
                emails = [email for email in emails if not email.get('is_read', True)]
            
            if since_date:
                since_iso = since_date.isoformat()
                emails = [
                    email for email in emails 
                    if email.get('timestamp', '') >= since_iso
                ]
            
            return emails
            
        except Exception as e:
            print(f"Error reading emails: {e}")
            raise
    
    async def get_email_by_id(
        self, 
        user_id: str, 
        account_id: str, 
        message_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific email by its message ID.
        
        Args:
            user_id: User identifier
            account_id: Email account identifier
            message_id: Message identifier
            
        Returns:
            Email dictionary or None if not found
        """
        try:
            # Get all emails and find the specific one
            emails = await self.get_emails(user_id, account_id, limit=1000)
            
            for email in emails:
                if email.get('id') == message_id:
                    return email
            
            return None
            
        except Exception as e:
            print(f"Error getting email by ID: {e}")
            raise
    
    async def mark_as_read(
        self, 
        user_id: str, 
        account_id: str, 
        message_id: str
    ) -> bool:
        """
        Mark an email as read.
        
        Args:
            user_id: User identifier
            account_id: Email account identifier
            message_id: Message identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update the email status in database
            result = self.provider_manager.supabase.schema('email_provider').from_('email_messages').update({
                'is_read': True,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('account_id', account_id).eq('message_id', message_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error marking email as read: {e}")
            return False
    
    async def mark_as_unread(
        self, 
        user_id: str, 
        account_id: str, 
        message_id: str
    ) -> bool:
        """
        Mark an email as unread.
        
        Args:
            user_id: User identifier
            account_id: Email account identifier
            message_id: Message identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update the email status in database
            result = self.provider_manager.supabase.schema('email_provider').from_('email_messages').update({
                'is_read': False,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('account_id', account_id).eq('message_id', message_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error marking email as unread: {e}")
            return False
    
    async def search_emails(
        self, 
        user_id: str, 
        account_id: str, 
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search emails by query string.
        
        Args:
            user_id: User identifier
            account_id: Email account identifier
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching emails
        """
        try:
            # Get emails and filter by query
            emails = await self.get_emails(user_id, account_id, limit=1000)
            
            # Simple text search in subject, sender, and body
            query_lower = query.lower()
            matching_emails = []
            
            for email in emails:
                if (query_lower in email.get('subject', '').lower() or
                    query_lower in email.get('sender', '').lower() or
                    query_lower in email.get('body', '').lower()):
                    matching_emails.append(email)
                    
                    if len(matching_emails) >= limit:
                        break
            
            return matching_emails
            
        except Exception as e:
            print(f"Error searching emails: {e}")
            raise
    
    async def get_user_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all email accounts for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of email account dictionaries
        """
        try:
            return await self.provider_manager.get_user_email_accounts(user_id)
        except Exception as e:
            print(f"Error getting user accounts: {e}")
            raise
