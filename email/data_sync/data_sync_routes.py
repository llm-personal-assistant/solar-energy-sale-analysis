"""
API routes for email data synchronization.
Provides endpoints for syncing emails from Gmail and Outlook accounts.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from .models import EmailSyncRequest, EmailSyncResult, EmailMessage, EmailAccount
from .email_sync_service import EmailSyncService
from .gmail_service import GmailService
from .outlook_service import OutlookService
from common.supabase_client import get_supabase_client

# Import auth dependencies
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.auth_routes import get_current_user_from_token
from auth.models import UserResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/data-sync", tags=["Email Data Sync"])

# Initialize services
supabase = get_supabase_client()
email_sync_service = EmailSyncService(supabase)
gmail_service = GmailService()
outlook_service = OutlookService()


class SyncEmailsRequest(BaseModel):
    """Request model for syncing emails."""
    account_id: Optional[str] = Field(None, description="Specific account ID to sync")
    provider: Optional[str] = Field(None, description="Provider to sync (google, outlook)")
    max_messages: int = Field(100, ge=1, le=1000, description="Maximum number of messages to sync")
    folder: Optional[str] = Field(None, description="Specific folder to sync (inbox, sent, etc.)")
    background_sync: bool = Field(False, description="Whether to run sync in background")


class SyncEmailsResponse(BaseModel):
    """Response model for email sync."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


class EmailAccountInfo(BaseModel):
    """Email account information."""
    id: str
    email: str
    provider: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserAccountsResponse(BaseModel):
    """Response model for user accounts."""
    accounts: List[EmailAccountInfo]
    total: int


class SyncStatusResponse(BaseModel):
    """Response model for sync status."""
    total_messages: int
    unread_messages: int
    folder_counts: Dict[str, int]
    latest_sync: Optional[datetime]


class MessagesResponse(BaseModel):
    """Response model for messages."""
    messages: List[EmailMessage]
    total: int
    page: int
    limit: int


@router.get("/accounts", response_model=UserAccountsResponse)
async def get_user_email_accounts(
    current_user: UserResponse = Depends(get_current_user_from_token),
    active_only: bool = Query(True, description="Only return active accounts")
):
    """Get all email accounts for a user."""
    try:
        # Build query
        query = supabase.schema('email_provider').from_('email_accounts')\
            .select("id, email, provider, is_active, created_at, updated_at")\
            .eq("user_id", current_user.id)
        
        if active_only:
            query = query.eq("is_active", True)
        
        result = query.execute()
        
        accounts = []
        for account_data in result.data:
            account = EmailAccountInfo(
                id=account_data["id"],
                email=account_data["email"],
                provider=account_data["provider"],
                is_active=account_data["is_active"],
                created_at=datetime.fromisoformat(account_data["created_at"].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(account_data["updated_at"].replace('Z', '+00:00'))
            )
            accounts.append(account)
        
        return UserAccountsResponse(
            accounts=accounts,
            total=len(accounts)
        )
        
    except Exception as e:
        logger.error(f"Error getting email accounts for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get email accounts: {str(e)}")


@router.post("/sync", response_model=SyncEmailsResponse)
async def sync_emails(
    request: SyncEmailsRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user_from_token)
):
    """Sync emails for a user from their email accounts."""
    try:
        # Create sync request
        sync_request = EmailSyncRequest(
            user_id=current_user.id,
            account_id=request.account_id,
            provider=request.provider,
            max_messages=request.max_messages,
            folder=request.folder
        )
        
        if request.background_sync:
            # Run sync in background
            background_tasks.add_task(
                _background_sync_emails,
                sync_request
            )
            
            return SyncEmailsResponse(
                success=True,
                message="Email sync started in background",
                data={"background_sync": True}
            )
        else:
            # Run sync synchronously
            result = await email_sync_service.sync_emails_for_user(sync_request)
            
            return SyncEmailsResponse(
                success=result.success,
                message=f"Synced {result.messages_synced} messages",
                data={
                    "messages_synced": result.messages_synced,
                    "messages_created": result.messages_created,
                    "messages_updated": result.messages_updated,
                    "sync_time": result.sync_time.isoformat()
                },
                errors=result.errors if result.errors else None
            )
            
    except Exception as e:
        logger.error(f"Error syncing emails for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sync emails: {str(e)}")


@router.post("/sync/account/{account_id}", response_model=SyncEmailsResponse)
async def sync_account_emails(
    account_id: str,
    current_user: UserResponse = Depends(get_current_user_from_token),
    max_messages: int = Query(100, ge=1, le=1000, description="Maximum number of messages to sync"),
    folder: Optional[str] = Query(None, description="Specific folder to sync"),
    background_sync: bool = Query(False, description="Whether to run sync in background")
):
    """Sync emails for a specific account."""
    try:
        # Get account information
        account_result = supabase.schema('email_provider').from_('email_accounts')\
            .select("*")\
            .eq("id", account_id)\
            .eq("user_id", current_user.id)\
            .eq("is_active", True)\
            .execute()
        
        if not account_result.data:
            raise HTTPException(status_code=404, detail="Account not found or inactive")
        
        account_data = account_result.data[0]
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
        
        if background_sync:
            # Run sync in background
            background_tasks = BackgroundTasks()
            background_tasks.add_task(
                _background_sync_account,
                account,
                current_user.id,
                max_messages,
                folder
            )
            
            return SyncEmailsResponse(
                success=True,
                message=f"Email sync started in background for account {account.email}",
                data={"background_sync": True, "account_email": account.email}
            )
        else:
            # Run sync synchronously
            result = await email_sync_service.sync_emails_for_account(
                account, current_user.id, max_messages, folder
            )
            
            return SyncEmailsResponse(
                success=result.success,
                message=f"Synced {result.messages_synced} messages from {account.email}",
                data={
                    "account_email": account.email,
                    "messages_synced": result.messages_synced,
                    "messages_created": result.messages_created,
                    "messages_updated": result.messages_updated,
                    "sync_time": result.sync_time.isoformat()
                },
                errors=result.errors if result.errors else None
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing emails for account {account_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sync account emails: {str(e)}")


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    current_user: UserResponse = Depends(get_current_user_from_token)
):
    """Get sync status for a user."""
    try:
        status = await email_sync_service.get_sync_status(current_user.id)
        
        return SyncStatusResponse(
            total_messages=status["total_messages"],
            unread_messages=status["unread_messages"],
            folder_counts=status["folder_counts"],
            latest_sync=datetime.fromisoformat(status["latest_sync"]) if status["latest_sync"] else None
        )
        
    except Exception as e:
        logger.error(f"Error getting sync status for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")


@router.get("/messages", response_model=MessagesResponse)
async def get_user_messages(
    current_user: UserResponse = Depends(get_current_user_from_token),
    limit: int = Query(50, ge=1, le=500, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    folder: Optional[str] = Query(None, description="Filter by folder"),
    unread_only: bool = Query(False, description="Only return unread messages")
):
    """Get messages for a user."""
    try:
        # Build query
        query = supabase.table("email_message")\
            .select("*")\
            .eq("user_id", current_user.id)\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)
        
        if folder:
            query = query.eq("folder", folder)
        
        if unread_only:
            query = query.eq("is_read", False)
        
        result = query.execute()
        
        messages = []
        for msg_data in result.data:
            message = EmailMessage(
                message_id=msg_data["message_id"],
                lead_id=msg_data.get("lead_id"),
                user_id=msg_data["user_id"],
                owner=msg_data.get("owner"),
                sender=msg_data.get("sender"),
                receiver=msg_data.get("receiver"),
                subject=msg_data.get("subject"),
                body=msg_data.get("body"),
                is_read=msg_data["is_read"],
                folder=msg_data.get("folder"),
                raw_data=msg_data.get("raw_data"),
                summary=msg_data.get("summary"),
                internal_date=msg_data.get("internal_date"),
                history_id=msg_data.get("history_id"),
                created_at=datetime.fromisoformat(msg_data["created_at"].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(msg_data["updated_at"].replace('Z', '+00:00'))
            )
            messages.append(message)
        
        # Get total count
        count_query = supabase.table("email_message")\
            .select("message_id", count="exact")\
            .eq("user_id", current_user.id)
        
        if folder:
            count_query = count_query.eq("folder", folder)
        
        if unread_only:
            count_query = count_query.eq("is_read", False)
        
        count_result = count_query.execute()
        total = count_result.count if count_result.count else 0
        
        return MessagesResponse(
            messages=messages,
            total=total,
            page=offset // limit + 1,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error getting messages for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.patch("/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: str,
    current_user: UserResponse = Depends(get_current_user_from_token)
):
    """Mark a message as read."""
    try:
        result = await email_sync_service.mark_message_as_read(message_id, current_user.id)
        
        if result.success:
            return {"success": True, "message": "Message marked as read"}
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking message {message_id} as read: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to mark message as read: {str(e)}")


@router.get("/folders/{provider}")
async def get_provider_folders(
    provider: str,
    current_user: UserResponse = Depends(get_current_user_from_token),
    account_id: Optional[str] = Query(None, description="Specific account ID")
):
    """Get available folders for a provider."""
    try:
        # Get account information
        query = supabase.schema('email_provider').from_('email_accounts')\
            .select("*")\
            .eq("user_id", current_user.id)\
            .eq("provider", provider)\
            .eq("is_active", True)
        
        if account_id:
            query = query.eq("id", account_id)
        
        result = query.execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No active accounts found for provider")
        
        # Use first account to get folders
        account_data = result.data[0]
        
        if provider.lower() == "google":
            gmail_service.authenticate_with_tokens(
                account_data["access_token"],
                account_data.get("refresh_token")
            )
            folders = gmail_service.get_folders()
        elif provider.lower() == "outlook":
            outlook_service.authenticate_with_token(account_data["access_token"])
            folders = outlook_service.get_folders()
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
        
        return {
            "provider": provider,
            "account_email": account_data["email"],
            "folders": folders
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting folders for provider {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get folders: {str(e)}")


# Background task functions
async def _background_sync_emails(sync_request: EmailSyncRequest):
    """Background task for syncing emails."""
    try:
        logger.info(f"Starting background email sync for user {sync_request.user_id}")
        result = await email_sync_service.sync_emails_for_user(sync_request)
        logger.info(f"Background email sync completed for user {sync_request.user_id}: {result.messages_synced} messages synced")
    except Exception as e:
        logger.error(f"Background email sync failed for user {sync_request.user_id}: {str(e)}")


async def _background_sync_account(account: EmailAccount, user_id: str, max_messages: int, folder: Optional[str]):
    """Background task for syncing account emails."""
    try:
        logger.info(f"Starting background email sync for account {account.email}")
        result = await email_sync_service.sync_emails_for_account(account, user_id, max_messages, folder)
        logger.info(f"Background email sync completed for account {account.email}: {result.messages_synced} messages synced")
    except Exception as e:
        logger.error(f"Background email sync failed for account {account.email}: {str(e)}")


# Health check endpoint
@router.get("/health")
async def health_check(current_user: UserResponse = Depends(get_current_user_from_token)):
    """Health check endpoint."""
    return {"status": "healthy", "service": "email-data-sync", "user_id": current_user.id}
