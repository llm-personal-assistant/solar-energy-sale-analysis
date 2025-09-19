from fastapi import FastAPI, HTTPException, Depends, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import os
import uuid
from dotenv import load_dotenv
import uvicorn
from datetime import datetime, timezone

try:
    from common.supabase_client import get_supabase_client
    from .email_service import EmailService
    from .models import (
        SendEmailRequest, SaveDraftRequest, EmailMessageResponse, 
        DraftEmailResponse, EmailStatus
    )
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from common.supabase_client import get_supabase_client
    from email_service import EmailService
    from models import (
        SendEmailRequest, SaveDraftRequest, EmailMessageResponse, 
        DraftEmailResponse, EmailStatus
    )

# Import auth module from parent directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.auth_routes import get_current_user_from_token

service_router = APIRouter(prefix="/email", tags=["email"])
security = HTTPBearer()
# Load environment variables
load_dotenv()

# Initialize email service
email_service = EmailService()

@service_router.get("/")
async def root():
    return {"message": "Email Service API is running"}

@service_router.get("/email-accounts")
async def get_email_accounts(current_user = Depends(get_current_user_from_token)):
    """Get all email accounts for the current user"""
    try:
        accounts = await email_service.get_user_email_accounts(current_user.id)
        return [
            {
                "id": account['id'],
                "email": account['email'],
                "provider": account['provider'],
                "is_active": account['is_active'],
                "created_at": account['created_at']
            }
            for account in accounts
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@service_router.get("/emails/{account_id}", response_model=List[EmailMessageResponse])
async def get_emails(
    account_id: str,
    limit: int = 50,
    current_user = Depends(get_current_user_from_token)
):
    """Get emails from a specific account"""
    try:
        emails = await email_service.get_emails(
            user_id=current_user.id,
            account_id=account_id,
            limit=limit
        )
        return [
            EmailMessageResponse(
                id=email['id'],
                subject=email['subject'],
                sender=email['sender'],
                recipient=email['recipient'],
                body=email['body'],
                timestamp=email['timestamp'],
                is_read=email['is_read'],
                status=EmailStatus.RECEIVED
            )
            for email in emails
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@service_router.post("/send-email/{account_id}")
async def send_email(
    account_id: str,
    email_request: SendEmailRequest,
    current_user = Depends(get_current_user_from_token)
):
    """Send email using a specific account"""
    try:
        result = await email_service.send_email(
            user_id=current_user.id,
            account_id=account_id,
            to_emails=email_request.to,
            subject=email_request.subject,
            body=email_request.body,
            is_html=email_request.is_html
        )
        return {"message": "Email sent successfully", "message_id": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@service_router.post("/save-draft/{account_id}", response_model=DraftEmailResponse)
async def save_draft(
    account_id: str,
    draft_request: SaveDraftRequest,
    current_user = Depends(get_current_user_from_token)
):
    """Save email as draft"""
    try:
        # Verify account belongs to user
        accounts = await email_service.get_user_email_accounts(current_user.id)
        account_exists = any(account['id'] == account_id for account in accounts)
        if not account_exists:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Save draft
        draft = await email_service.save_draft(
            user_id=current_user.id,
            account_id=account_id,
            to_emails=draft_request.to,
            subject=draft_request.subject,
            body=draft_request.body,
            is_html=draft_request.is_html
        )
        
        return DraftEmailResponse(
            id=draft['id'],
            to=draft['to'],
            subject=draft['subject'],
            body=draft['body'],
            is_html=draft['is_html'],
            created_at=draft['created_at'],
            updated_at=draft['updated_at']
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@service_router.get("/drafts", response_model=List[DraftEmailResponse])
async def get_drafts(current_user = Depends(get_current_user_from_token)):
    """Get all draft emails for the current user"""
    try:
        drafts = await email_service.get_drafts(current_user.id)
        return [
            DraftEmailResponse(
                id=draft['id'],
                to=draft['to'],
                subject=draft['subject'],
                body=draft['body'],
                is_html=draft['is_html'],
                created_at=draft['created_at'],
                updated_at=draft['updated_at']
            )
            for draft in drafts
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@service_router.get("/drafts/{draft_id}", response_model=DraftEmailResponse)
async def get_draft(
    draft_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Get a specific draft email"""
    try:
        draft = await email_service.get_draft(current_user.id, draft_id)
        return DraftEmailResponse(
            id=draft['id'],
            to=draft['to'],
            subject=draft['subject'],
            body=draft['body'],
            is_html=draft['is_html'],
            created_at=draft['created_at'],
            updated_at=draft['updated_at']
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@service_router.put("/drafts/{draft_id}", response_model=DraftEmailResponse)
async def update_draft(
    draft_id: str,
    draft_request: SaveDraftRequest,
    current_user = Depends(get_current_user_from_token)
):
    """Update a draft email"""
    try:
        draft = await email_service.update_draft(
            user_id=current_user.id,
            draft_id=draft_id,
            to_emails=draft_request.to,
            subject=draft_request.subject,
            body=draft_request.body,
            is_html=draft_request.is_html
        )
        
        return DraftEmailResponse(
            id=draft['id'],
            to=draft['to'],
            subject=draft['subject'],
            body=draft['body'],
            is_html=draft['is_html'],
            created_at=draft['created_at'],
            updated_at=draft['updated_at']
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@service_router.delete("/drafts/{draft_id}")
async def delete_draft(
    draft_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Delete a draft email"""
    try:
        await email_service.delete_draft(current_user.id, draft_id)
        return {"message": "Draft deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@service_router.post("/send-draft/{draft_id}/{account_id}")
async def send_draft(
    draft_id: str,
    account_id: str,
    current_user = Depends(get_current_user_from_token)
):
    """Send a draft email"""
    try:
        result = await email_service.send_draft(
            user_id=current_user.id,
            draft_id=draft_id,
            account_id=account_id
        )
        return {"message": "Draft sent successfully", "message_id": result}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

email_app = FastAPI(
    title="Email Service API",
    description="API for managing emails and drafts with Supabase",
    version="1.0.0"
)

# CORS middleware
email_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
email_app.include_router(service_router)

if __name__ == "__main__":
    uvicorn.run(email_app, host="0.0.0.0", port=8001)