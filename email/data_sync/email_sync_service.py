"""
Unified email sync service for Gmail and Outlook.
Handles email synchronization from multiple providers to the database.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from supabase import Client
try:
    from .models import (
        EmailMessage, EmailMessageCreate, EmailMessageUpdate,
        EmailAccount, EmailSyncRequest, EmailSyncResult, DataSyncResponse
    )
    from .gmail_service import GmailService
    from .outlook_service import OutlookService
    from common.supabase_client import get_supabase_client
except Exception as e:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models import (
        EmailMessage, EmailMessageCreate, EmailMessageUpdate,
        EmailAccount, EmailSyncRequest, EmailSyncResult, DataSyncResponse
    )
    from gmail_service import GmailService
    from outlook_service import OutlookService
    from common.supabase_client import get_supabase_client
logger = logging.getLogger(__name__)


class EmailSyncService:
    """Unified service for syncing emails from multiple providers."""
    
    def __init__(self, supabase_client: Client):
        """Initialize the email sync service."""
        self.supabase = get_supabase_client().get_admin_client()
        self.gmail_service = GmailService()
        self.outlook_service = OutlookService()
        self.schema = "email"
        self.message_table = "email_message"
        self.account_table = "email_accounts"
    
    async def get_user_email_accounts(self, user_id: str) -> List[EmailAccount]:
        """Get all email accounts for a user."""
        try:
            result = self.supabase.schema("email_provider").from_(self.account_table)\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .execute()
            
            accounts = []
            for account_data in result.data:
                account = EmailAccount(
                    id=account_data["id"],
                    user_id=account_data["user_id"],
                    email=account_data["email"],
                    provider=account_data["provider"],
                    access_token=account_data["access_token"],
                    refresh_token=account_data.get("refresh_token"),
                    is_active=account_data["is_active"],
                    created_at=datetime.fromisoformat(account_data["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(account_data["updated_at"].replace('Z', '+00:00'))
                )
                accounts.append(account)
            
            return accounts
            
        except Exception as e:
            logger.error(f"Error getting email accounts for user {user_id}: {str(e)}")
            return []
    
    async def sync_emails_for_user(self, sync_request: EmailSyncRequest) -> EmailSyncResult:
        """Sync emails for a user from all their accounts."""
        try:
            # Get user's email accounts
            accounts = await self.get_user_email_accounts(sync_request.user_id)
            if not accounts:
                return EmailSyncResult(
                    success=False,
                    messages_synced=0,
                    errors=["No active email accounts found for user"]
                )
            
            # Filter accounts if specific criteria provided
            # if sync_request.account_id:
            #     accounts = [acc for acc in accounts if acc.id == sync_request.account_id]
            # elif sync_request.provider:
            #     accounts = [acc for acc in accounts if acc.provider == sync_request.provider]
            
            total_messages_synced = 0
            total_messages_created = 0
            total_messages_updated = 0
            all_errors = []
            
            # Sync each account
            for account in accounts:
                try:
                    result = await self.sync_emails_for_account(
                        account, 
                        sync_request.user_id,
                        sync_request.max_messages,
                        sync_request.folder
                    )
                    
                    total_messages_synced += result.messages_synced
                    total_messages_created += result.messages_created
                    total_messages_updated += result.messages_updated
                    all_errors.extend(result.errors)
                    
                except Exception as e:
                    error_msg = f"Error syncing account {account.email}: {str(e)}"
                    logger.error(error_msg)
                    all_errors.append(error_msg)
            
            return EmailSyncResult(
                success=len(all_errors) == 0,
                messages_synced=total_messages_synced,
                messages_created=total_messages_created,
                messages_updated=total_messages_updated,
                errors=all_errors
            )
            
        except Exception as e:
            logger.error(f"Error syncing emails for user {sync_request.user_id}: {str(e)}")
            return EmailSyncResult(
                success=False,
                messages_synced=0,
                errors=[str(e)]
            )
    
    async def sync_emails_for_account(self, account: EmailAccount, user_id: str, 
                                    max_messages: int = 100, folder: Optional[str] = None) -> EmailSyncResult:
        """Sync emails for a specific account."""
        try:
            # Get emails from provider
            if account.provider.lower() == 'google':
                email_messages = self.gmail_service.sync_emails_to_database(
                    account, user_id, max_messages, folder
                )
            elif account.provider.lower() == 'outlook':
                email_messages = self.outlook_service.sync_emails_to_database(
                    account, user_id, max_messages, folder
                )
            else:
                return EmailSyncResult(
                    success=False,
                    messages_synced=0,
                    errors=[f"Unsupported provider: {account.provider}"]
                )
            
            if not email_messages:
                return EmailSyncResult(
                    success=True,
                    messages_synced=0,
                    errors=[]
                )
            # Sync to database
            return await self._sync_messages_to_database(email_messages, user_id)
            
        except Exception as e:
            logger.error(f"Error syncing emails for account {account.email}: {str(e)}")
            return EmailSyncResult(
                success=False,
                messages_synced=0,
                errors=[str(e)]
            )
    
    async def _sync_messages_to_database(self, email_messages: List[EmailMessageCreate], 
                                       user_id: str) -> EmailSyncResult:
        """Sync email messages to the database."""
        try:
            messages_created = 0
            messages_updated = 0
            errors = []
            
            for email_msg in email_messages:
                try:
                    # Check if message already exists
                    existing_msg = await self._get_message_by_id(email_msg.message_id, user_id)
                    
                    if existing_msg:
                        logger.info(f"Message already exists: {email_msg.message_id}")
                        # Update existing message
                        # update_data = EmailMessageUpdate(
                        #     lead_id=email_msg.lead_id,
                        #     owner=email_msg.owner,
                        #     sender=email_msg.sender,
                        #     receiver=email_msg.receiver,
                        #     subject=email_msg.subject,
                        #     body=email_msg.body,
                        #     is_read=email_msg.is_read,
                        #     folder=email_msg.folder,
                        #     raw_data=email_msg.raw_data,
                        #     summary=email_msg.summary,
                        #     internal_date=email_msg.internal_date,
                        #     history_id=email_msg.history_id
                        # )
                        
                        # result = await self._update_message(email_msg.message_id, update_data, user_id)
                        # if result.success:
                        #     messages_updated += 1
                        # else:
                        #     errors.append(f"Failed to update message {email_msg.message_id}: {result.message}")
                    else:
                        # Create new message
                        result = await self._create_message(email_msg, user_id)
                        if result.success:
                            messages_created += 1
                        else:
                            errors.append(f"Failed to create message {email_msg.message_id}: {result.message}")
                            
                except Exception as e:
                    error_msg = f"Error processing message {email_msg.message_id}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            return EmailSyncResult(
                success=len(errors) == 0,
                messages_synced=messages_created + messages_updated,
                messages_created=messages_created,
                messages_updated=messages_updated,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error syncing messages to database: {str(e)}")
            return EmailSyncResult(
                success=False,
                messages_synced=0,
                errors=[str(e)]
            )
    
    async def _get_message_by_id(self, message_id: str, user_id: str) -> Optional[EmailMessage]:
        """Get a message by ID."""
        try:
            result = self.supabase.schema(self.schema).from_(self.message_table)\
                .select("*")\
                .eq("message_id", message_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if result.data:
                return EmailMessage(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {str(e)}")
            return None
    
    async def _create_message(self, email_msg: EmailMessageCreate, user_id: str) -> DataSyncResponse:
        """Create a new email message."""
        try:
            # Prepare data for insertion
            message_dict = email_msg.dict()
            message_dict["user_id"] = user_id
            message_dict["created_at"] = datetime.utcnow().isoformat()
            message_dict["updated_at"] = datetime.utcnow().isoformat()
            
            # Insert into Supabase
            result = self.supabase.schema(self.schema).from_(self.message_table).insert(message_dict).execute()
            
            if result.data:
                return DataSyncResponse(
                    success=True,
                    message="Message created successfully",
                    data={"message_id": result.data[0]["message_id"]}
                )
            else:
                return DataSyncResponse(
                    success=False,
                    message="Failed to create message",
                    errors=["No data returned from database"]
                )
                
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            return DataSyncResponse(
                success=False,
                message="Error creating message",
                errors=[str(e)]
            )
    
    async def _update_message(self, message_id: str, update_data: EmailMessageUpdate, 
                            user_id: str) -> DataSyncResponse:
        """Update an existing email message."""
        try:
            # Prepare update data
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            update_dict["updated_at"] = datetime.utcnow().isoformat()
            
            # Update in Supabase
            result = self.supabase.schema(self.schema).from_(self.message_table)\
                .update(update_dict)\
                .eq("message_id", message_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if result.data:
                return DataSyncResponse(
                    success=True,
                    message="Message updated successfully",
                    data={"message_id": message_id}
                )
            else:
                return DataSyncResponse(
                    success=False,
                    message="Message not found or update failed",
                    errors=["No data returned from database"]
                )
                
        except Exception as e:
            logger.error(f"Error updating message {message_id}: {str(e)}")
            return DataSyncResponse(
                success=False,
                message="Error updating message",
                errors=[str(e)]
            )
    
    async def get_user_messages(self, user_id: str, limit: int = 100, offset: int = 0, 
                               folder: Optional[str] = None) -> List[EmailMessage]:
        """Get messages for a user."""
        try:
            query = self.supabase.schema(self.schema).from_(self.message_table)\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)
            
            if folder:
                query = query.eq("folder", folder)
            
            result = query.execute()
            
            return [EmailMessage(**msg) for msg in result.data]
            
        except Exception as e:
            logger.error(f"Error getting messages for user {user_id}: {str(e)}")
            return []
    
    async def get_unread_count(self, user_id: str, folder: Optional[str] = None) -> int:
        """Get unread message count for a user."""
        try:
            query = self.supabase.schema(self.schema).from_(self.message_table)\
                .select("message_id", count="exact")\
                .eq("user_id", user_id)\
                .eq("is_read", False)
            
            if folder:
                query = query.eq("folder", folder)
            
            result = query.execute()
            return result.count if result.count else 0
            
        except Exception as e:
            logger.error(f"Error getting unread count for user {user_id}: {str(e)}")
            return 0
    
    async def mark_message_as_read(self, message_id: str, user_id: str) -> DataSyncResponse:
        """Mark a message as read."""
        try:
            result = self.supabase.schema(self.schema).from_(self.message_table)\
                .update({"is_read": True, "updated_at": datetime.utcnow().isoformat()})\
                .eq("message_id", message_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if result.data:
                return DataSyncResponse(
                    success=True,
                    message="Message marked as read"
                )
            else:
                return DataSyncResponse(
                    success=False,
                    message="Message not found or update failed"
                )
                
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            return DataSyncResponse(
                success=False,
                message="Error marking message as read",
                errors=[str(e)]
            )
    
    async def get_sync_status(self, user_id: str) -> Dict[str, Any]:
        """Get sync status for a user."""
        try:
            # Get total message count
            total_result = self.supabase.schema(self.schema).from_(self.message_table)\
                .select("message_id", count="exact")\
                .eq("user_id", user_id)\
                .execute()
            
            # Get unread count
            unread_result = self.supabase.schema(self.schema).from_(self.message_table)\
                .select("message_id", count="exact")\
                .eq("user_id", user_id)\
                .eq("is_read", False)\
                .execute()
            
            # Get messages by folder
            folder_result = self.supabase.schema(self.schema).from_(self.message_table)\
                .select("folder")\
                .eq("user_id", user_id)\
                .execute()
            
            folder_counts = {}
            for msg in folder_result.data:
                folder = msg["folder"] or "unknown"
                folder_counts[folder] = folder_counts.get(folder, 0) + 1
            
            # Get latest sync time
            latest_result = self.supabase.schema(self.schema).from_(self.message_table)\
                .select("created_at")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            latest_sync = None
            if latest_result.data:
                latest_sync = latest_result.data[0]["created_at"]
            
            return {
                "total_messages": total_result.count if total_result.count else 0,
                "unread_messages": unread_result.count if unread_result.count else 0,
                "folder_counts": folder_counts,
                "latest_sync": latest_sync
            }
            
        except Exception as e:
            logger.error(f"Error getting sync status for user {user_id}: {str(e)}")
            return {
                "total_messages": 0,
                "unread_messages": 0,
                "folder_counts": {},
                "latest_sync": None
            }
