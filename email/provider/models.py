from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

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
    created_at: datetime

class OAuthState(BaseModel):
    state: str
    user_id: str
    provider: str
    created_at: datetime
    expires_at: datetime
