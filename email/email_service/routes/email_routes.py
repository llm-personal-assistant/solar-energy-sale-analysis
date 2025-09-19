"""
Email Reading Routes

FastAPI routes for reading and managing emails.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from email_service import EmailService

router = APIRouter(prefix="/emails", tags=["emails"])

# Initialize email service
email_service = EmailService()


class EmailResponse(BaseModel):
    """Response model for email data."""
    id: str
    subject: str
    sender: str
    recipient: str
    body: str
    timestamp: str
    is_read: bool


class EmailListResponse(BaseModel):
    """Response model for email list."""
    emails: List[EmailResponse]
    total: int
    limit: int
    offset: int


class MarkReadRequest(BaseModel):
    """Request model for marking email as read."""
    message_id: str


class MarkUnreadRequest(BaseModel):
    """Request model for marking email as unread."""
    message_id: str


@router.get("/{user_id}/{account_id}", response_model=EmailListResponse)
async def get_emails(
    user_id: str = Path(..., description="User ID"),
    account_id: str = Path(..., description="Email account ID"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of emails to retrieve"),
    offset: int = Query(0, ge=0, description="Number of emails to skip"),
    unread_only: bool = Query(False, description="Only return unread emails"),
    since_date: Optional[str] = Query(None, description="Only return emails since this date (ISO format)")
):
    """
    Get emails from a specific account.
    
    Args:
        user_id: User identifier
        account_id: Email account identifier
        limit: Maximum number of emails to retrieve
        offset: Number of emails to skip
        unread_only: Only return unread emails
        since_date: Only return emails since this date (ISO format)
    """
    try:
        # Parse since_date if provided
        since_datetime = None
        if since_date:
            try:
                since_datetime = datetime.fromisoformat(since_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")
        
        # Get emails
        emails = await email_service.get_emails(
            user_id=user_id,
            account_id=account_id,
            limit=limit + offset,  # Get more to handle offset
            unread_only=unread_only,
            since_date=since_datetime
        )
        
        # Apply offset
        emails = emails[offset:offset + limit]
        
        # Convert to response format
        email_responses = [
            EmailResponse(
                id=email['id'],
                subject=email['subject'],
                sender=email['sender'],
                recipient=email['recipient'],
                body=email['body'],
                timestamp=email['timestamp'],
                is_read=email['is_read']
            )
            for email in emails
        ]
        
        return EmailListResponse(
            emails=email_responses,
            total=len(email_responses),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving emails: {str(e)}")


@router.get("/{user_id}/{account_id}/{message_id}", response_model=EmailResponse)
async def get_email_by_id(
    user_id: str = Path(..., description="User ID"),
    account_id: str = Path(..., description="Email account ID"),
    message_id: str = Path(..., description="Message ID")
):
    """
    Get a specific email by its message ID.
    
    Args:
        user_id: User identifier
        account_id: Email account identifier
        message_id: Message identifier
    """
    try:
        email = await email_service.get_email_by_id(user_id, account_id, message_id)
        
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        return EmailResponse(
            id=email['id'],
            subject=email['subject'],
            sender=email['sender'],
            recipient=email['recipient'],
            body=email['body'],
            timestamp=email['timestamp'],
            is_read=email['is_read']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving email: {str(e)}")


@router.post("/{user_id}/{account_id}/mark-read")
async def mark_email_as_read(
    user_id: str = Path(..., description="User ID"),
    account_id: str = Path(..., description="Email account ID"),
    request: MarkReadRequest = ...
):
    """
    Mark an email as read.
    
    Args:
        user_id: User identifier
        account_id: Email account identifier
        request: Request containing message ID
    """
    try:
        success = await email_service.mark_as_read(user_id, account_id, request.message_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Email not found or could not be marked as read")
        
        return {"success": True, "message": "Email marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking email as read: {str(e)}")


@router.post("/{user_id}/{account_id}/mark-unread")
async def mark_email_as_unread(
    user_id: str = Path(..., description="User ID"),
    account_id: str = Path(..., description="Email account ID"),
    request: MarkUnreadRequest = ...
):
    """
    Mark an email as unread.
    
    Args:
        user_id: User identifier
        account_id: Email account identifier
        request: Request containing message ID
    """
    try:
        success = await email_service.mark_as_unread(user_id, account_id, request.message_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Email not found or could not be marked as unread")
        
        return {"success": True, "message": "Email marked as unread"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking email as unread: {str(e)}")


@router.get("/{user_id}/{account_id}/search")
async def search_emails(
    user_id: str = Path(..., description="User ID"),
    account_id: str = Path(..., description="Email account ID"),
    query: str = Query(..., description="Search query"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results")
):
    """
    Search emails by query string.
    
    Args:
        user_id: User identifier
        account_id: Email account identifier
        query: Search query
        limit: Maximum number of results
    """
    try:
        emails = await email_service.search_emails(user_id, account_id, query, limit)
        
        # Convert to response format
        email_responses = [
            EmailResponse(
                id=email['id'],
                subject=email['subject'],
                sender=email['sender'],
                recipient=email['recipient'],
                body=email['body'],
                timestamp=email['timestamp'],
                is_read=email['is_read']
            )
            for email in emails
        ]
        
        return {
            "emails": email_responses,
            "total": len(email_responses),
            "query": query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching emails: {str(e)}")


@router.get("/{user_id}/statistics")
async def get_email_statistics(
    user_id: str = Path(..., description="User ID"),
    account_id: Optional[str] = Query(None, description="Specific account ID (optional)")
):
    """
    Get email statistics for a user.
    
    Args:
        user_id: User identifier
        account_id: Specific account ID (optional)
    """
    try:
        stats = await email_service.get_email_statistics(user_id, account_id)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting email statistics: {str(e)}")
