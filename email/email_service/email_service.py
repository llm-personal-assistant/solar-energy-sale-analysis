"""
Main Email Service Module

Provides a unified interface for all email operations including reading, sending, and draft management.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path to import provider modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from provider.email_providers import EmailProviderManager
try:
    from .email_reader import EmailReader
    from .email_sender import EmailSender
    from .draft_manager import DraftManager
except ImportError:
    from email_reader import EmailReader
    from email_sender import EmailSender
    from draft_manager import DraftManager


class EmailService:
    """
    Main email service that provides unified access to all email operations.
    """
    
    def __init__(self):
        self.provider_manager = EmailProviderManager()
        self.reader = EmailReader()
        self.sender = EmailSender()
        self.draft_manager = DraftManager()
    
    # Email Reading Operations
    async def get_emails(
        self, 
        user_id: str, 
        account_id: str, 
        limit: int = 50,
        unread_only: bool = False,
        since_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get emails from a specific account."""
        return await self.reader.get_emails(user_id, account_id, limit, unread_only, since_date)
    
    async def get_email_by_id(
        self, 
        user_id: str, 
        account_id: str, 
        message_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific email by its message ID."""
        return await self.reader.get_email_by_id(user_id, account_id, message_id)
    
    async def mark_as_read(
        self, 
        user_id: str, 
        account_id: str, 
        message_id: str
    ) -> bool:
        """Mark an email as read."""
        return await self.reader.mark_as_read(user_id, account_id, message_id)
    
    async def mark_as_unread(
        self, 
        user_id: str, 
        account_id: str, 
        message_id: str
    ) -> bool:
        """Mark an email as unread."""
        return await self.reader.mark_as_unread(user_id, account_id, message_id)
    
    async def search_emails(
        self, 
        user_id: str, 
        account_id: str, 
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search emails by query string."""
        return await self.reader.search_emails(user_id, account_id, query, limit)
    
    # Email Sending Operations
    async def send_email(
        self,
        user_id: str,
        account_id: str,
        to_emails: List[str],
        subject: str,
        body: str,
        is_html: bool = False,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send an email."""
        return await self.sender.send_email(
            user_id, account_id, to_emails, subject, body, 
            is_html, cc_emails, bcc_emails, attachments
        )
    
    async def send_bulk_email(
        self,
        user_id: str,
        account_id: str,
        email_list: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """Send emails in bulk with rate limiting."""
        return await self.sender.send_bulk_email(user_id, account_id, email_list, batch_size)
    
    async def get_sent_emails(
        self,
        user_id: str,
        account_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get history of sent emails."""
        return await self.sender.get_sent_emails(user_id, account_id, limit)
    
    # Draft Management Operations
    async def create_draft(
        self,
        user_id: str,
        account_id: str,
        to_emails: List[str],
        subject: str,
        body: str,
        is_html: bool = False,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create a new email draft."""
        return await self.draft_manager.create_draft(
            user_id, account_id, to_emails, subject, body, 
            is_html, cc_emails, bcc_emails, attachments
        )
    
    async def update_draft(
        self,
        user_id: str,
        draft_id: str,
        **updates
    ) -> Dict[str, Any]:
        """Update an existing email draft."""
        return await self.draft_manager.update_draft(user_id, draft_id, **updates)
    
    async def get_draft(
        self,
        user_id: str,
        draft_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific draft by ID."""
        return await self.draft_manager.get_draft(user_id, draft_id)
    
    async def get_user_drafts(
        self,
        user_id: str,
        account_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all drafts for a user."""
        return await self.draft_manager.get_user_drafts(user_id, account_id, limit)
    
    async def delete_draft(
        self,
        user_id: str,
        draft_id: str
    ) -> bool:
        """Delete a draft."""
        return await self.draft_manager.delete_draft(user_id, draft_id)
    
    async def send_draft(
        self,
        user_id: str,
        draft_id: str
    ) -> Dict[str, Any]:
        """Send a draft email."""
        return await self.draft_manager.send_draft(user_id, draft_id)
    
    async def duplicate_draft(
        self,
        user_id: str,
        draft_id: str
    ) -> Dict[str, Any]:
        """Duplicate an existing draft."""
        return await self.draft_manager.duplicate_draft(user_id, draft_id)
    
    async def search_drafts(
        self,
        user_id: str,
        query: str,
        account_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search drafts by query string."""
        return await self.draft_manager.search_drafts(user_id, query, account_id, limit)
    
    # Account Management Operations
    async def get_user_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all email accounts for a user."""
        return await self.reader.get_user_accounts(user_id)
    
    async def get_auth_url(self, provider: str, user_id: str) -> str:
        """Get OAuth authorization URL for a provider."""
        return await self.provider_manager.get_auth_url(provider, user_id)
    
    async def handle_oauth_callback(self, user_id: str, provider: str, code: str) -> Dict[str, Any]:
        """Handle OAuth callback and create email account."""
        return await self.provider_manager.handle_oauth_callback(user_id, provider, code)
    
    async def validate_and_consume_state(self, state: str, provider: str) -> str:
        """Validate OAuth state and return user ID."""
        return await self.provider_manager.validate_and_consume_state(state, provider)
    
    # Utility Operations
    async def get_email_statistics(
        self,
        user_id: str,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get email statistics for a user or account.
        
        Args:
            user_id: User identifier
            account_id: Email account identifier (optional)
            
        Returns:
            Dictionary with email statistics
        """
        try:
            stats = {
                'total_emails': 0,
                'unread_emails': 0,
                'sent_emails': 0,
                'drafts': 0,
                'accounts': 0
            }
            
            # Get account count
            accounts = await self.get_user_accounts(user_id)
            stats['accounts'] = len(accounts)
            
            # Get email counts for each account
            for account in accounts:
                if account_id and account['id'] != account_id:
                    continue
                
                # Get total emails
                emails = await self.get_emails(user_id, account['id'], limit=1000)
                stats['total_emails'] += len(emails)
                
                # Get unread emails
                unread_emails = await self.get_emails(user_id, account['id'], limit=1000, unread_only=True)
                stats['unread_emails'] += len(unread_emails)
                
                # Get sent emails
                sent_emails = await self.get_sent_emails(user_id, account['id'], limit=1000)
                stats['sent_emails'] += len(sent_emails)
                
                # Get drafts
                drafts = await self.get_user_drafts(user_id, account['id'], limit=1000)
                stats['drafts'] += len(drafts)
            
            return stats
            
        except Exception as e:
            print(f"Error getting email statistics: {e}")
            return {
                'total_emails': 0,
                'unread_emails': 0,
                'sent_emails': 0,
                'drafts': 0,
                'accounts': 0,
                'error': str(e)
            }
    
    async def cleanup_old_data(
        self,
        user_id: str,
        days_old: int = 30
    ) -> Dict[str, Any]:
        """
        Clean up old email data.
        
        Args:
            user_id: User identifier
            days_old: Number of days to keep data
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            cutoff_iso = cutoff_date.isoformat()
            
            results = {
                'deleted_drafts': 0,
                'deleted_sent_emails': 0,
                'errors': []
            }
            
            # Clean up old drafts
            try:
                draft_result = self.provider_manager.supabase.schema('email_provider').from_('email_drafts').delete().eq('user_id', user_id).lt('created_at', cutoff_iso).execute()
                results['deleted_drafts'] = len(draft_result.data) if draft_result.data else 0
            except Exception as e:
                results['errors'].append(f"Error deleting old drafts: {e}")
            
            # Clean up old sent emails
            try:
                sent_result = self.provider_manager.supabase.schema('email_provider').from_('sent_emails').delete().eq('user_id', user_id).lt('sent_at', cutoff_iso).execute()
                results['deleted_sent_emails'] = len(sent_result.data) if sent_result.data else 0
            except Exception as e:
                results['errors'].append(f"Error deleting old sent emails: {e}")
            
            return results
            
        except Exception as e:
            print(f"Error in cleanup: {e}")
            return {
                'deleted_drafts': 0,
                'deleted_sent_emails': 0,
                'errors': [str(e)]
            }
