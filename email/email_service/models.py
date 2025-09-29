from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

# class EmailStatus(str, Enum):
#     DRAFT = "draft"
#     SENT = "sent"
#     RECEIVED = "received"

class User(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

class EmailAccount(BaseModel):
    id: str
    user_id: str
    email: EmailStr
    provider: str  # 'google', 'outlook', 'yahoo'
    access_token: str
    refresh_token: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class EmailMessage(BaseModel):
    id: str
    account_id: str
    message_id: str  # Provider's message ID
    subject: str
    sender: str
    recipient: str
    body: str
    timestamp: datetime
    is_read: bool = False
    # status: EmailStatus = EmailStatus.RECEIVED
    created_at: datetime

class DraftEmail(BaseModel):
    id: str
    user_id: str
    account_id: str
    to: List[EmailStr]
    subject: str
    body: str
    is_html: bool = False
    created_at: datetime
    updated_at: datetime

class SendEmailRequest(BaseModel):
    to: List[EmailStr]
    subject: str
    body: str
    is_html: bool = False

class SaveDraftRequest(BaseModel):
    to: List[EmailStr]
    subject: str
    body: str
    is_html: bool = False

class EmailMessageResponse(BaseModel):
    id: str
    lead_id: str
    subject: str
    sender: str
    recipient: str
    body: str
    summary: str
    internal_date: datetime
    is_read: bool
    # status: EmailStatus

class LeadResponse(BaseModel):
    id: str
    owner: str
    subject: str
    internal_date: datetime

class DraftEmailResponse(BaseModel):
    id: str
    to: List[EmailStr]
    subject: str
    body: str
    is_html: bool
    created_at: str
    updated_at: str

class OAuthState(BaseModel):
    state: str
    user_id: str
    provider: str
    created_at: datetime
    expires_at: datetime
