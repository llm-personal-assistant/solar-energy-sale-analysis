"""
Email Sender Module

Handles sending emails through various providers with automatic token refresh.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path to import provider modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from provider.email_providers import EmailProviderManager


class EmailSender:
    """Handles sending emails through connected email accounts."""
    
    def __init__(self):
        self.provider_manager = EmailProviderManager()
    
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
        """
        Send an email.
        
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
            Dictionary with send result information
        """
        try:
            # Validate inputs
            if not to_emails:
                raise ValueError("At least one recipient email is required")
            
            if not subject.strip():
                raise ValueError("Email subject is required")
            
            if not body.strip():
                raise ValueError("Email body is required")
            
            # Get account details
            accounts = await self.provider_manager.get_user_email_accounts(user_id)
            account = next((acc for acc in accounts if acc['id'] == account_id), None)
            
            if not account:
                raise ValueError("Email account not found")
            
            # Prepare email content
            email_content = self._prepare_email_content(
                to_emails, subject, body, is_html, cc_emails, bcc_emails
            )
            
            # Send email through provider
            message_id = await self.provider_manager.send_email(
                user_id=user_id,
                account_id=account_id,
                to_emails=to_emails,
                subject=subject,
                body=email_content,
                is_html=is_html
            )
            
            # Log the sent email
            await self._log_sent_email(
                user_id, account_id, message_id, to_emails, 
                subject, email_content, cc_emails, bcc_emails
            )
            
            return {
                'success': True,
                'message_id': message_id,
                'sent_at': datetime.now(timezone.utc).isoformat(),
                'recipients': to_emails,
                'cc': cc_emails or [],
                'bcc': bcc_emails or []
            }
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return {
                'success': False,
                'error': str(e),
                'sent_at': datetime.now(timezone.utc).isoformat()
            }
    
    def _prepare_email_content(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        is_html: bool,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None
    ) -> str:
        """
        Prepare email content with proper formatting.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Email body content
            is_html: Whether the body is HTML format
            cc_emails: List of CC email addresses
            bcc_emails: List of BCC email addresses
            
        Returns:
            Formatted email content
        """
        if is_html:
            # For HTML emails, wrap in proper HTML structure
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{subject}</title>
            </head>
            <body>
                {body}
            </body>
            </html>
            """
            return html_content
        else:
            # For plain text emails, add proper formatting
            text_content = f"""
{body}

---
Sent via Email Service
"""
            return text_content
    
    async def _log_sent_email(
        self,
        user_id: str,
        account_id: str,
        message_id: str,
        to_emails: List[str],
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None
    ):
        """
        Log sent email to database for tracking.
        
        Args:
            user_id: User identifier
            account_id: Email account identifier
            message_id: Message identifier from provider
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Email body content
            cc_emails: List of CC email addresses
            bcc_emails: List of BCC email addresses
        """
        try:
            sent_email_data = {
                'user_id': user_id,
                'account_id': account_id,
                'message_id': message_id,
                'subject': subject,
                'recipients': ','.join(to_emails),
                'cc_recipients': ','.join(cc_emails) if cc_emails else None,
                'bcc_recipients': ','.join(bcc_emails) if bcc_emails else None,
                'body_preview': body[:500] + '...' if len(body) > 500 else body,
                'sent_at': datetime.now(timezone.utc).isoformat(),
                'status': 'sent'
            }
            
            # Insert into sent_emails table (you may need to create this table)
            self.provider_manager.supabase.schema('email_provider').from_('sent_emails').insert(sent_email_data).execute()
            
        except Exception as e:
            print(f"Error logging sent email: {e}")
    
    async def send_bulk_email(
        self,
        user_id: str,
        account_id: str,
        email_list: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Send emails in bulk with rate limiting.
        
        Args:
            user_id: User identifier
            account_id: Email account identifier
            email_list: List of email dictionaries
            batch_size: Number of emails to send in each batch
            
        Returns:
            Dictionary with bulk send results
        """
        try:
            results = {
                'total': len(email_list),
                'successful': 0,
                'failed': 0,
                'errors': []
            }
            
            # Process emails in batches
            for i in range(0, len(email_list), batch_size):
                batch = email_list[i:i + batch_size]
                
                # Send emails in parallel within each batch
                tasks = []
                for email_data in batch:
                    task = self.send_email(
                        user_id=user_id,
                        account_id=account_id,
                        to_emails=email_data.get('to_emails', []),
                        subject=email_data.get('subject', ''),
                        body=email_data.get('body', ''),
                        is_html=email_data.get('is_html', False),
                        cc_emails=email_data.get('cc_emails'),
                        bcc_emails=email_data.get('bcc_emails')
                    )
                    tasks.append(task)
                
                # Wait for batch to complete
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in batch_results:
                    if isinstance(result, Exception):
                        results['failed'] += 1
                        results['errors'].append(str(result))
                    elif result.get('success'):
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append(result.get('error', 'Unknown error'))
                
                # Add delay between batches to respect rate limits
                if i + batch_size < len(email_list):
                    await asyncio.sleep(1)
            
            return results
            
        except Exception as e:
            print(f"Error in bulk email sending: {e}")
            return {
                'total': len(email_list),
                'successful': 0,
                'failed': len(email_list),
                'errors': [str(e)]
            }
    
    async def get_sent_emails(
        self,
        user_id: str,
        account_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get history of sent emails.
        
        Args:
            user_id: User identifier
            account_id: Email account identifier (optional)
            limit: Maximum number of emails to retrieve
            
        Returns:
            List of sent email dictionaries
        """
        try:
            query = self.provider_manager.supabase.schema('email_provider').from_('sent_emails').select('*').eq('user_id', user_id)
            
            if account_id:
                query = query.eq('account_id', account_id)
            
            result = query.order('sent_at', desc=True).limit(limit).execute()
            return result.data
            
        except Exception as e:
            print(f"Error getting sent emails: {e}")
            raise
