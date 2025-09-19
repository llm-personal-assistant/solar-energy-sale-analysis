"""
Draft Management Routes

FastAPI routes for managing email drafts.
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from email_service import EmailService

router = APIRouter(prefix="/drafts", tags=["drafts"])

# Initialize email service
email_service = EmailService()


class CreateDraftRequest(BaseModel):
    """Request model for creating a draft."""
    to_emails: List[EmailStr]
    subject: str
    body: str
    is_html: bool = False
    cc_emails: Optional[List[EmailStr]] = None
    bcc_emails: Optional[List[EmailStr]] = None
    attachments: Optional[List[dict]] = None


class UpdateDraftRequest(BaseModel):
    """Request model for updating a draft."""
    to_emails: Optional[List[EmailStr]] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    is_html: Optional[bool] = None
    cc_emails: Optional[List[EmailStr]] = None
    bcc_emails: Optional[List[EmailStr]] = None
    attachments: Optional[List[dict]] = None


class DraftResponse(BaseModel):
    """Response model for draft data."""
    id: str
    user_id: str
    account_id: str
    to_emails: List[str]
    subject: str
    body: str
    is_html: bool
    cc_emails: List[str]
    bcc_emails: List[str]
    attachments: List[dict]
    created_at: str
    updated_at: str
    status: str
    sent_at: Optional[str] = None


class DraftListResponse(BaseModel):
    """Response model for draft list."""
    drafts: List[DraftResponse]
    total: int
    limit: int
    offset: int


class CreateDraftResponse(BaseModel):
    """Response model for draft creation."""
    success: bool
    draft_id: Optional[str] = None
    draft: Optional[DraftResponse] = None
    error: Optional[str] = None


class UpdateDraftResponse(BaseModel):
    """Response model for draft update."""
    success: bool
    draft: Optional[DraftResponse] = None
    error: Optional[str] = None


class SendDraftResponse(BaseModel):
    """Response model for sending a draft."""
    success: bool
    message_id: Optional[str] = None
    sent_at: Optional[str] = None
    error: Optional[str] = None


@router.post("/{user_id}/{account_id}", response_model=CreateDraftResponse)
async def create_draft(
    user_id: str = Path(..., description="User ID"),
    account_id: str = Path(..., description="Email account ID"),
    request: CreateDraftRequest = ...
):
    """
    Create a new email draft.
    
    Args:
        user_id: User identifier
        account_id: Email account identifier
        request: Draft creation request
    """
    try:
        result = await email_service.create_draft(
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
        
        if result['success']:
            draft_data = result['draft']
            draft_response = DraftResponse(
                id=draft_data['id'],
                user_id=draft_data['user_id'],
                account_id=draft_data['account_id'],
                to_emails=draft_data['to_emails'],
                subject=draft_data['subject'],
                body=draft_data['body'],
                is_html=draft_data['is_html'],
                cc_emails=draft_data['cc_emails'],
                bcc_emails=draft_data['bcc_emails'],
                attachments=draft_data['attachments'],
                created_at=draft_data['created_at'],
                updated_at=draft_data['updated_at'],
                status=draft_data['status']
            )
            
            return CreateDraftResponse(
                success=True,
                draft_id=result['draft_id'],
                draft=draft_response
            )
        else:
            return CreateDraftResponse(
                success=False,
                error=result['error']
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating draft: {str(e)}")


@router.put("/{user_id}/{draft_id}", response_model=UpdateDraftResponse)
async def update_draft(
    user_id: str = Path(..., description="User ID"),
    draft_id: str = Path(..., description="Draft ID"),
    request: UpdateDraftRequest = ...
):
    """
    Update an existing email draft.
    
    Args:
        user_id: User identifier
        draft_id: Draft identifier
        request: Draft update request
    """
    try:
        # Convert request to dict, excluding None values
        updates = {}
        for field, value in request.dict().items():
            if value is not None:
                updates[field] = value
        
        result = await email_service.update_draft(user_id, draft_id, **updates)
        
        if result['success']:
            draft_data = result['draft']
            draft_response = DraftResponse(
                id=draft_data['id'],
                user_id=draft_data['user_id'],
                account_id=draft_data['account_id'],
                to_emails=draft_data['to_emails'],
                subject=draft_data['subject'],
                body=draft_data['body'],
                is_html=draft_data['is_html'],
                cc_emails=draft_data['cc_emails'],
                bcc_emails=draft_data['bcc_emails'],
                attachments=draft_data['attachments'],
                created_at=draft_data['created_at'],
                updated_at=draft_data['updated_at'],
                status=draft_data['status'],
                sent_at=draft_data.get('sent_at')
            )
            
            return UpdateDraftResponse(
                success=True,
                draft=draft_response
            )
        else:
            return UpdateDraftResponse(
                success=False,
                error=result['error']
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating draft: {str(e)}")


@router.get("/{user_id}/{draft_id}", response_model=DraftResponse)
async def get_draft(
    user_id: str = Path(..., description="User ID"),
    draft_id: str = Path(..., description="Draft ID")
):
    """
    Get a specific draft by ID.
    
    Args:
        user_id: User identifier
        draft_id: Draft identifier
    """
    try:
        draft = await email_service.get_draft(user_id, draft_id)
        
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        return DraftResponse(
            id=draft['id'],
            user_id=draft['user_id'],
            account_id=draft['account_id'],
            to_emails=draft['to_emails'],
            subject=draft['subject'],
            body=draft['body'],
            is_html=draft['is_html'],
            cc_emails=draft['cc_emails'],
            bcc_emails=draft['bcc_emails'],
            attachments=draft['attachments'],
            created_at=draft['created_at'],
            updated_at=draft['updated_at'],
            status=draft['status'],
            sent_at=draft.get('sent_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving draft: {str(e)}")


@router.get("/{user_id}", response_model=DraftListResponse)
async def get_user_drafts(
    user_id: str = Path(..., description="User ID"),
    account_id: Optional[str] = Query(None, description="Email account ID (optional)"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of drafts to retrieve"),
    offset: int = Query(0, ge=0, description="Number of drafts to skip")
):
    """
    Get all drafts for a user.
    
    Args:
        user_id: User identifier
        account_id: Email account identifier (optional)
        limit: Maximum number of drafts to retrieve
        offset: Number of drafts to skip
    """
    try:
        drafts = await email_service.get_user_drafts(user_id, account_id, limit + offset)
        
        # Apply offset
        drafts = drafts[offset:offset + limit]
        
        # Convert to response format
        draft_responses = [
            DraftResponse(
                id=draft['id'],
                user_id=draft['user_id'],
                account_id=draft['account_id'],
                to_emails=draft['to_emails'],
                subject=draft['subject'],
                body=draft['body'],
                is_html=draft['is_html'],
                cc_emails=draft['cc_emails'],
                bcc_emails=draft['bcc_emails'],
                attachments=draft['attachments'],
                created_at=draft['created_at'],
                updated_at=draft['updated_at'],
                status=draft['status'],
                sent_at=draft.get('sent_at')
            )
            for draft in drafts
        ]
        
        return DraftListResponse(
            drafts=draft_responses,
            total=len(draft_responses),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving drafts: {str(e)}")


@router.delete("/{user_id}/{draft_id}")
async def delete_draft(
    user_id: str = Path(..., description="User ID"),
    draft_id: str = Path(..., description="Draft ID")
):
    """
    Delete a draft.
    
    Args:
        user_id: User identifier
        draft_id: Draft identifier
    """
    try:
        success = await email_service.delete_draft(user_id, draft_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Draft not found or could not be deleted")
        
        return {"success": True, "message": "Draft deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting draft: {str(e)}")


@router.post("/{user_id}/{draft_id}/send", response_model=SendDraftResponse)
async def send_draft(
    user_id: str = Path(..., description="User ID"),
    draft_id: str = Path(..., description="Draft ID")
):
    """
    Send a draft email.
    
    Args:
        user_id: User identifier
        draft_id: Draft identifier
    """
    try:
        result = await email_service.send_draft(user_id, draft_id)
        
        return SendDraftResponse(
            success=result['success'],
            message_id=result.get('message_id'),
            sent_at=result.get('sent_at'),
            error=result.get('error')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending draft: {str(e)}")


@router.post("/{user_id}/{draft_id}/duplicate", response_model=CreateDraftResponse)
async def duplicate_draft(
    user_id: str = Path(..., description="User ID"),
    draft_id: str = Path(..., description="Draft ID")
):
    """
    Duplicate an existing draft.
    
    Args:
        user_id: User identifier
        draft_id: Draft identifier
    """
    try:
        result = await email_service.duplicate_draft(user_id, draft_id)
        
        if result['success']:
            draft_data = result['draft']
            draft_response = DraftResponse(
                id=draft_data['id'],
                user_id=draft_data['user_id'],
                account_id=draft_data['account_id'],
                to_emails=draft_data['to_emails'],
                subject=draft_data['subject'],
                body=draft_data['body'],
                is_html=draft_data['is_html'],
                cc_emails=draft_data['cc_emails'],
                bcc_emails=draft_data['bcc_emails'],
                attachments=draft_data['attachments'],
                created_at=draft_data['created_at'],
                updated_at=draft_data['updated_at'],
                status=draft_data['status']
            )
            
            return CreateDraftResponse(
                success=True,
                draft_id=result['draft_id'],
                draft=draft_response
            )
        else:
            return CreateDraftResponse(
                success=False,
                error=result['error']
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error duplicating draft: {str(e)}")


@router.get("/{user_id}/search")
async def search_drafts(
    user_id: str = Path(..., description="User ID"),
    query: str = Query(..., description="Search query"),
    account_id: Optional[str] = Query(None, description="Email account ID (optional)"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results")
):
    """
    Search drafts by query string.
    
    Args:
        user_id: User identifier
        query: Search query
        account_id: Email account identifier (optional)
        limit: Maximum number of results
    """
    try:
        drafts = await email_service.search_drafts(user_id, query, account_id, limit)
        
        # Convert to response format
        draft_responses = [
            DraftResponse(
                id=draft['id'],
                user_id=draft['user_id'],
                account_id=draft['account_id'],
                to_emails=draft['to_emails'],
                subject=draft['subject'],
                body=draft['body'],
                is_html=draft['is_html'],
                cc_emails=draft['cc_emails'],
                bcc_emails=draft['bcc_emails'],
                attachments=draft['attachments'],
                created_at=draft['created_at'],
                updated_at=draft['updated_at'],
                status=draft['status'],
                sent_at=draft.get('sent_at')
            )
            for draft in drafts
        ]
        
        return {
            "drafts": draft_responses,
            "total": len(draft_responses),
            "query": query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching drafts: {str(e)}")
