from fastapi import FastAPI, HTTPException, Depends, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import os
import uuid
from dotenv import load_dotenv
import uvicorn

try:
    from common.supabase_client import get_supabase_client
    from .email_providers import EmailProviderManager
    from .models import User, EmailAccount
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from common.supabase_client import get_supabase_client
    from email_providers import EmailProviderManager
    from models import User, EmailAccount

# Import auth module from parent directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.auth_routes import get_current_user_from_token

provider_router = APIRouter(prefix="/auth", tags=["provider"])
security = HTTPBearer()
# Load environment variables
load_dotenv()


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

# Email-related models moved to email_service module

@provider_router.get("/")
async def root():
    return {"message": "Email Provider API is running"}

@provider_router.post("/register-email-provider", response_model=EmailAccountResponse)
async def register_email_provider(
    registration: UserRegistration,
    current_user = Depends(get_current_user_from_token)
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
            user_id=current_user.id,
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

@provider_router.get("/email-accounts", response_model=List[EmailAccountResponse])
async def get_email_accounts(current_user = Depends(get_current_user_from_token)):
    """Get all email accounts for the current user"""
    try:
        accounts = await email_manager.get_user_email_accounts(current_user.id)
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

# Email functionality moved to email_service module

@provider_router.get("/auth-url/{provider}")
async def get_auth_url(provider: str, current_user = Depends(get_current_user_from_token)):
    """Get OAuth URL for email provider authentication"""
    try:
        if provider not in ['google', 'outlook', 'yahoo']:
            raise HTTPException(
                status_code=400,
                detail="Invalid provider. Must be 'google', 'outlook', or 'yahoo'"
            )
        print(f"Getting auth URL for provider: {provider}")
        user_id = str(uuid.uuid4())
        auth_url = await email_manager.get_auth_url(provider, current_user)
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@provider_router.get("/oauth-callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str,
    state: str
):
    """Handle OAuth callback and create email account"""
    try:
        # Validate state and get associated user_id
        print(f"Validating state: {state} for provider: {provider}")

        user_id = await email_manager.validate_and_consume_state(state, provider)
        print(f"User ID: {user_id}")
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

provider_app = FastAPI(
    title="Email Provider API",
    description="API for managing email providers (Google, Outlook, Yahoo) with Supabase",
    version="1.0.0"
)

# CORS middleware
provider_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
provider_app.include_router(provider_router)

if __name__ == "__main__":
    uvicorn.run(provider_app, host="0.0.0.0", port=8000)
