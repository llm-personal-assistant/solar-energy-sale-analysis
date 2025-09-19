"""
Draft Manager Module

Handles email draft creation, editing, and management.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import sys
import os
import uuid

# Add parent directory to path to import provider modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from provider.email_providers import EmailProviderManager


class DraftManager:
    """Handles email draft management."""
    
    def __init__(self):
        self.provider_manager = EmailProviderManager()
    
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
        """
        Create a new email draft.
        
        Args:
            user_id: User identifier
            account_id: Email account identifier
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Email body content
            is_html: Whether the body is HTML format
            cc_emails: List of CC email addresses
            bcc_emails: List of BCC email addresses
            attachments: List of attachment dictionaries
            
        Returns:
            Dictionary with draft information
        """
        try:
            draft_id = str(uuid.uuid4())
            
            draft_data = {
                'id': draft_id,
                'user_id': user_id,
                'account_id': account_id,
                'to_emails': to_emails,
                'subject': subject,
                'body': body,
                'is_html': is_html,
                'cc_emails': cc_emails or [],
                'bcc_emails': bcc_emails or [],
                'attachments': attachments or [],
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'status': 'draft'
            }
            
            # Save draft to database
            result = self.provider_manager.supabase.schema('email_provider').from_('email_drafts').insert(draft_data).execute()
            
            return {
                'success': True,
                'draft_id': draft_id,
                'draft': result.data[0] if result.data else draft_data
            }
            
        except Exception as e:
            print(f"Error creating draft: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_draft(
        self,
        user_id: str,
        draft_id: str,
        **updates
    ) -> Dict[str, Any]:
        """
        Update an existing email draft.
        
        Args:
            user_id: User identifier
            draft_id: Draft identifier
            **updates: Fields to update
            
        Returns:
            Dictionary with update result
        """
        try:
            # Add updated timestamp
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Update draft in database
            result = self.provider_manager.supabase.schema('email_provider').from_('email_drafts').update(updates).eq('id', draft_id).eq('user_id', user_id).execute()
            
            if result.data:
                return {
                    'success': True,
                    'draft': result.data[0]
                }
            else:
                return {
                    'success': False,
                    'error': 'Draft not found'
                }
                
        except Exception as e:
            print(f"Error updating draft: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_draft(
        self,
        user_id: str,
        draft_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific draft by ID.
        
        Args:
            user_id: User identifier
            draft_id: Draft identifier
            
        Returns:
            Draft dictionary or None if not found
        """
        try:
            result = self.provider_manager.supabase.schema('email_provider').from_('email_drafts').select('*').eq('id', draft_id).eq('user_id', user_id).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"Error getting draft: {e}")
            return None
    
    async def get_user_drafts(
        self,
        user_id: str,
        account_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all drafts for a user.
        
        Args:
            user_id: User identifier
            account_id: Email account identifier (optional)
            limit: Maximum number of drafts to retrieve
            
        Returns:
            List of draft dictionaries
        """
        try:
            query = self.provider_manager.supabase.schema('email_provider').from_('email_drafts').select('*').eq('user_id', user_id)
            
            if account_id:
                query = query.eq('account_id', account_id)
            
            result = query.order('updated_at', desc=True).limit(limit).execute()
            return result.data
            
        except Exception as e:
            print(f"Error getting user drafts: {e}")
            return []
    
    async def delete_draft(
        self,
        user_id: str,
        draft_id: str
    ) -> bool:
        """
        Delete a draft.
        
        Args:
            user_id: User identifier
            draft_id: Draft identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.provider_manager.supabase.schema('email_provider').from_('email_drafts').delete().eq('id', draft_id).eq('user_id', user_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error deleting draft: {e}")
            return False
    
    async def send_draft(
        self,
        user_id: str,
        draft_id: str
    ) -> Dict[str, Any]:
        """
        Send a draft email.
        
        Args:
            user_id: User identifier
            draft_id: Draft identifier
            
        Returns:
            Dictionary with send result
        """
        try:
            # Get the draft
            draft = await self.get_draft(user_id, draft_id)
            if not draft:
                return {
                    'success': False,
                    'error': 'Draft not found'
                }
            
            # Import EmailSender to send the email
            from .email_sender import EmailSender
            email_sender = EmailSender()
            
            # Send the email
            send_result = await email_sender.send_email(
                user_id=user_id,
                account_id=draft['account_id'],
                to_emails=draft['to_emails'],
                subject=draft['subject'],
                body=draft['body'],
                is_html=draft.get('is_html', False),
                cc_emails=draft.get('cc_emails'),
                bcc_emails=draft.get('bcc_emails'),
                attachments=draft.get('attachments')
            )
            
            if send_result.get('success'):
                # Mark draft as sent
                await self.update_draft(user_id, draft_id, status='sent', sent_at=send_result['sent_at'])
                
                return {
                    'success': True,
                    'message_id': send_result['message_id'],
                    'sent_at': send_result['sent_at']
                }
            else:
                return {
                    'success': False,
                    'error': send_result.get('error', 'Failed to send email')
                }
                
        except Exception as e:
            print(f"Error sending draft: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def duplicate_draft(
        self,
        user_id: str,
        draft_id: str
    ) -> Dict[str, Any]:
        """
        Duplicate an existing draft.
        
        Args:
            user_id: User identifier
            draft_id: Draft identifier
            
        Returns:
            Dictionary with new draft information
        """
        try:
            # Get the original draft
            original_draft = await self.get_draft(user_id, draft_id)
            if not original_draft:
                return {
                    'success': False,
                    'error': 'Original draft not found'
                }
            
            # Create a new draft with the same content
            new_draft_result = await self.create_draft(
                user_id=user_id,
                account_id=original_draft['account_id'],
                to_emails=original_draft['to_emails'],
                subject=f"Copy of {original_draft['subject']}",
                body=original_draft['body'],
                is_html=original_draft.get('is_html', False),
                cc_emails=original_draft.get('cc_emails'),
                bcc_emails=original_draft.get('bcc_emails'),
                attachments=original_draft.get('attachments')
            )
            
            return new_draft_result
            
        except Exception as e:
            print(f"Error duplicating draft: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def search_drafts(
        self,
        user_id: str,
        query: str,
        account_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search drafts by query string.
        
        Args:
            user_id: User identifier
            query: Search query
            account_id: Email account identifier (optional)
            limit: Maximum number of results
            
        Returns:
            List of matching drafts
        """
        try:
            # Get all drafts and filter by query
            drafts = await self.get_user_drafts(user_id, account_id, limit=1000)
            
            # Simple text search in subject and body
            query_lower = query.lower()
            matching_drafts = []
            
            for draft in drafts:
                if (query_lower in draft.get('subject', '').lower() or
                    query_lower in draft.get('body', '').lower()):
                    matching_drafts.append(draft)
                    
                    if len(matching_drafts) >= limit:
                        break
            
            return matching_drafts
            
        except Exception as e:
            print(f"Error searching drafts: {e}")
            return []
