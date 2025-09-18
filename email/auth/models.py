from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserSignUp(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserSignIn(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
