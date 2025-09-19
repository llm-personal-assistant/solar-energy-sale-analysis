"""
Email Sending Routes

FastAPI routes for sending emails and managing sent email history.
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from email_service import EmailService

router = APIRouter(prefix="/send", tags=["send"])

# Initialize email service
email_service = EmailService()


class SendEmailRequest(BaseModel):
    """Request model for sending an email."""
    to_emails: List[EmailStr]
    subject: str
    body: str
    is_html: bool = False
    cc_emails: Optional[List[EmailStr]] = None
    bcc_emails: Optional[List[EmailStr]] = None
    attachments: Optional[List[dict]] = None


class BulkEmailItem(BaseModel):
    """Model for individual email in bulk send."""
    to_emails: List[EmailStr]
    subject: str
    body: str
    is_html: bool = False
    cc_emails: Optional[List[EmailStr]] = None
    bcc_emails: Optional[List[EmailStr]] = None


class BulkSendRequest(BaseModel):
    """Request model for bulk email sending."""
    emails: List[BulkEmailItem]
    batch_size: int = 10


class SendEmailResponse(BaseModel):
    """Response model for email sending."""
    success: bool
    message_id: Optional[str] = None
    sent_at: str
    recipients: List[str]
    cc: List[str] = []
    bcc: List[str] = []
    error: Optional[str] = None


class BulkSendResponse(BaseModel):
    """Response model for bulk email sending."""
    total: int
    successful: int
    failed: int
    errors: List[str] = []


class SentEmailResponse(BaseModel):
    """Response model for sent email history."""
    id: str
    user_id: str
    account_id: str
    message_id: str
    subject: str
    recipients: str
    cc_recipients: Optional[str] = None
    bcc_recipients: Optional[str] = None
    body_preview: str
    sent_at: str
    status: str


@router.post("/{user_id}/{account_id}", response_model=SendEmailResponse)
async def send_email(
    user_id: str = Path(..., description="User ID"),
    account_id: str = Path(..., description="Email account ID"),
    request: SendEmailRequest = ...
):
    """
    Send an email.
    
    Args:
        user_id: User identifier
        account_id: Email account identifier
        request: Email sending request
    """
    try:
        result = await email_service.send_email(
            user_id=user_id,
            account_id=account_id,
            to_emails=request.to_emails,
            subject=request.subject,
            body=request.body,
            is_html=request.is_html,
            cc_emails=request.cc_emails,
            bcc_emails=request.bcc_emails,
            attachments=request.attachments
        )
        
        return SendEmailResponse(
            success=result['success'],
            message_id=result.get('message_id'),
            sent_at=result['sent_at'],
            recipients=result.get('recipients', []),
            cc=result.get('cc', []),
            bcc=result.get('bcc', []),
            error=result.get('error')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")


@router.post("/{user_id}/{account_id}/bulk", response_model=BulkSendResponse)
async def send_bulk_email(
    user_id: str = Path(..., description="User ID"),
    account_id: str = Path(..., description="Email account ID"),
    request: BulkSendRequest = ...
):
    """
    Send emails in bulk.
    
    Args:
        user_id: User identifier
        account_id: Email account identifier
        request: Bulk email sending request
    """
    try:
        # Convert request to the format expected by the service
        email_list = []
        for email_item in request.emails:
            email_list.append({
                'to_emails': email_item.to_emails,
                'subject': email_item.subject,
                'body': email_item.body,
                'is_html': email_item.is_html,
                'cc_emails': email_item.cc_emails,
                'bcc_emails': email_item.bcc_emails
            })
        
        result = await email_service.send_bulk_email(
            user_id=user_id,
            account_id=account_id,
            email_list=email_list,
            batch_size=request.batch_size
        )
        
        return BulkSendResponse(
            total=result['total'],
            successful=result['successful'],
            failed=result['failed'],
            errors=result.get('errors', [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending bulk emails: {str(e)}")


@router.get("/{user_id}/history", response_model=List[SentEmailResponse])
async def get_sent_emails(
    user_id: str = Path(..., description="User ID"),
    account_id: Optional[str] = Query(None, description="Email account ID (optional)"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of emails to retrieve")
):
    """
    Get history of sent emails.
    
    Args:
        user_id: User identifier
        account_id: Email account identifier (optional)
        limit: Maximum number of emails to retrieve
    """
    try:
        sent_emails = await email_service.get_sent_emails(user_id, account_id, limit)
        
        # Convert to response format
        sent_email_responses = [
            SentEmailResponse(
                id=email['id'],
                user_id=email['user_id'],
                account_id=email['account_id'],
                message_id=email['message_id'],
                subject=email['subject'],
                recipients=email['recipients'],
                cc_recipients=email.get('cc_recipients'),
                bcc_recipients=email.get('bcc_recipients'),
                body_preview=email['body_preview'],
                sent_at=email['sent_at'],
                status=email['status']
            )
            for email in sent_emails
        ]
        
        return sent_email_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sent emails: {str(e)}")


@router.get("/{user_id}/{account_id}/history", response_model=List[SentEmailResponse])
async def get_sent_emails_by_account(
    user_id: str = Path(..., description="User ID"),
    account_id: str = Path(..., description="Email account ID"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of emails to retrieve")
):
    """
    Get history of sent emails for a specific account.
    
    Args:
        user_id: User identifier
        account_id: Email account identifier
        limit: Maximum number of emails to retrieve
    """
    try:
        sent_emails = await email_service.get_sent_emails(user_id, account_id, limit)
        
        # Convert to response format
        sent_email_responses = [
            SentEmailResponse(
                id=email['id'],
                user_id=email['user_id'],
                account_id=email['account_id'],
                message_id=email['message_id'],
                subject=email['subject'],
                recipients=email['recipients'],
                cc_recipients=email.get('cc_recipients'),
                bcc_recipients=email.get('bcc_recipients'),
                body_preview=email['body_preview'],
                sent_at=email['sent_at'],
                status=email['status']
            )
            for email in sent_emails
        ]
        
        return sent_email_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sent emails: {str(e)}")


@router.delete("/{user_id}/history/cleanup")
async def cleanup_sent_emails(
    user_id: str = Path(..., description="User ID"),
    days_old: int = Query(30, ge=1, description="Number of days to keep sent emails")
):
    """
    Clean up old sent email history.
    
    Args:
        user_id: User identifier
        days_old: Number of days to keep sent emails
    """
    try:
        cleanup_result = await email_service.cleanup_old_data(user_id, days_old)
        
        return {
            "success": True,
            "deleted_sent_emails": cleanup_result.get('deleted_sent_emails', 0),
            "deleted_drafts": cleanup_result.get('deleted_drafts', 0),
            "errors": cleanup_result.get('errors', [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up sent emails: {str(e)}")
