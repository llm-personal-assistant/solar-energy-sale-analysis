from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import os
import uuid
from dotenv import load_dotenv
import uvicorn

from supabase_client import get_supabase_client
from email_providers import EmailProviderManager
from auth import verify_token, get_current_user
from models import User, EmailAccount, EmailMessage

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Email Provider API",
    description="API for managing email providers (Google, Outlook, Yahoo) with Supabase",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize email provider manager
email_manager = EmailProviderManager()

# Pydantic models for API
class UserRegistration(BaseModel):
    email: EmailStr
    provider: str  # 'google', 'outlook', 'yahoo'
    access_token: str
    refresh_token: Optional[str] = None

class EmailAccountResponse(BaseModel):
    id: str
    email: str
    provider: str
    is_active: bool
    created_at: str

class SendEmailRequest(BaseModel):
    to: List[EmailStr]
    subject: str
    body: str
    is_html: bool = False

class EmailMessageResponse(BaseModel):
    id: str
    subject: str
    sender: str
    recipient: str
    body: str
    timestamp: str
    is_read: bool

@app.get("/")
async def root():
    return {"message": "Email Provider API is running"}

@app.post("/register-email-provider", response_model=EmailAccountResponse)
async def register_email_provider(
    registration: UserRegistration,
    current_user: dict = Depends(get_current_user)
):
    """Register a new email provider for the user"""
    try:
        # Validate provider
        if registration.provider not in ['google', 'outlook', 'yahoo']:
            raise HTTPException(
                status_code=400,
                detail="Invalid provider. Must be 'google', 'outlook', or 'yahoo'"
            )
        
        # Create email account
        account = await email_manager.create_email_account(
            user_id=current_user['id'],
            email=registration.email,
            provider=registration.provider,
            access_token=registration.access_token,
            refresh_token=registration.refresh_token
        )
        
        return EmailAccountResponse(
            id=account['id'],
            email=account['email'],
            provider=account['provider'],
            is_active=account['is_active'],
            created_at=account['created_at']
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/email-accounts", response_model=List[EmailAccountResponse])
async def get_email_accounts(current_user: dict = Depends(get_current_user)):
    """Get all email accounts for the current user"""
    try:
        accounts = await email_manager.get_user_email_accounts(current_user['id'])
        return [
            EmailAccountResponse(
                id=account['id'],
                email=account['email'],
                provider=account['provider'],
                is_active=account['is_active'],
                created_at=account['created_at']
            )
            for account in accounts
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/emails/{account_id}", response_model=List[EmailMessageResponse])
async def get_emails(
    account_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get emails from a specific account"""
    try:
        emails = await email_manager.get_emails(
            user_id=current_user['id'],
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
                is_read=email['is_read']
            )
            for email in emails
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/send-email/{account_id}")
async def send_email(
    account_id: str,
    email_request: SendEmailRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send email using a specific account"""
    try:
        result = await email_manager.send_email(
            user_id=current_user['id'],
            account_id=account_id,
            to_emails=email_request.to,
            subject=email_request.subject,
            body=email_request.body,
            is_html=email_request.is_html
        )
        return {"message": "Email sent successfully", "message_id": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth-url/{provider}")
async def get_auth_url(provider: str):
    """Get OAuth URL for email provider authentication"""
    try:
        if provider not in ['google', 'outlook', 'yahoo']:
            raise HTTPException(
                status_code=400,
                detail="Invalid provider. Must be 'google', 'outlook', or 'yahoo'"
            )
        print(f"Getting auth URL for provider: {provider}")
        user_id = str(uuid.uuid4())
        auth_url = await email_manager.get_auth_url(provider, user_id)
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/oauth-callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str,
    state: str
):
    """Handle OAuth callback and create email account"""
    try:
        # Validate state and get associated user_id
        user_id = await email_manager.validate_and_consume_state(state, provider)
        
        account = await email_manager.handle_oauth_callback(
            user_id=user_id,
            provider=provider,
            code=code
        )
        
        return EmailAccountResponse(
            id=account['id'],
            email=account['email'],
            provider=account['provider'],
            is_active=account['is_active'],
            created_at=account['created_at']
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
