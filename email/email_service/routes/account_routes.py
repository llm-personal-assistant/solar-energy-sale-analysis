"""
Account Management Routes

FastAPI routes for managing email accounts and OAuth authentication.
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Optional
from pydantic import BaseModel
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from email_service import EmailService

router = APIRouter(prefix="/accounts", tags=["accounts"])

# Initialize email service
email_service = EmailService()


class AccountResponse(BaseModel):
    """Response model for email account data."""
    id: str
    user_id: str
    email: str
    provider: str
    is_active: bool
    created_at: str
    updated_at: str


class AccountListResponse(BaseModel):
    """Response model for account list."""
    accounts: List[AccountResponse]
    total: int


class AuthUrlResponse(BaseModel):
    """Response model for OAuth authorization URL."""
    auth_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """Request model for OAuth callback."""
    code: str
    state: str


class OAuthCallbackResponse(BaseModel):
    """Response model for OAuth callback."""
    success: bool
    account: Optional[AccountResponse] = None
    error: Optional[str] = None


@router.get("/{user_id}", response_model=AccountListResponse)
async def get_user_accounts(
    user_id: str = Path(..., description="User ID")
):
    """
    Get all email accounts for a user.
    
    Args:
        user_id: User identifier
    """
    try:
        accounts = await email_service.get_user_accounts(user_id)
        
        # Convert to response format
        account_responses = [
            AccountResponse(
                id=account['id'],
                user_id=account['user_id'],
                email=account['email'],
                provider=account['provider'],
                is_active=account['is_active'],
                created_at=account['created_at'],
                updated_at=account['updated_at']
            )
            for account in accounts
        ]
        
        return AccountListResponse(
            accounts=account_responses,
            total=len(account_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving accounts: {str(e)}")


@router.get("/{user_id}/auth-url/{provider}", response_model=AuthUrlResponse)
async def get_auth_url(
    user_id: str = Path(..., description="User ID"),
    provider: str = Path(..., description="Email provider (google, outlook, yahoo)")
):
    """
    Get OAuth authorization URL for connecting a new email account.
    
    Args:
        user_id: User identifier
        provider: Email provider name
    """
    try:
        if provider not in ['google', 'outlook', 'yahoo']:
            raise HTTPException(status_code=400, detail="Unsupported provider. Use: google, outlook, yahoo")
        
        auth_url = await email_service.get_auth_url(provider, user_id)
        
        # Extract state from URL (this is a simplified approach)
        # In a real implementation, you might want to return the state separately
        import re
        state_match = re.search(r'state=([^&]+)', auth_url)
        state = state_match.group(1) if state_match else "unknown"
        
        return AuthUrlResponse(
            auth_url=auth_url,
            state=state
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting auth URL: {str(e)}")


@router.post("/{user_id}/oauth-callback/{provider}", response_model=OAuthCallbackResponse)
async def handle_oauth_callback(
    user_id: str = Path(..., description="User ID"),
    provider: str = Path(..., description="Email provider"),
    request: OAuthCallbackRequest = ...
):
    """
    Handle OAuth callback and create email account.
    
    Args:
        user_id: User identifier
        provider: Email provider name
        request: OAuth callback request
    """
    try:
        if provider not in ['google', 'outlook', 'yahoo']:
            raise HTTPException(status_code=400, detail="Unsupported provider. Use: google, outlook, yahoo")
        
        # Validate the state first
        try:
            validated_user_id = await email_service.validate_and_consume_state(request.state, provider)
            if validated_user_id != user_id:
                raise HTTPException(status_code=400, detail="Invalid OAuth state")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid OAuth state: {str(e)}")
        
        # Handle the OAuth callback
        account = await email_service.handle_oauth_callback(user_id, provider, request.code)
        
        # Convert to response format
        account_response = AccountResponse(
            id=account['id'],
            user_id=account['user_id'],
            email=account['email'],
            provider=account['provider'],
            is_active=account['is_active'],
            created_at=account['created_at'],
            updated_at=account['updated_at']
        )
        
        return OAuthCallbackResponse(
            success=True,
            account=account_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return OAuthCallbackResponse(
            success=False,
            error=str(e)
        )


@router.get("/{user_id}/statistics")
async def get_account_statistics(
    user_id: str = Path(..., description="User ID")
):
    """
    Get email statistics for all accounts of a user.
    
    Args:
        user_id: User identifier
    """
    try:
        stats = await email_service.get_email_statistics(user_id)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting account statistics: {str(e)}")


@router.delete("/{user_id}/cleanup")
async def cleanup_user_data(
    user_id: str = Path(..., description="User ID"),
    days_old: int = Query(30, ge=1, description="Number of days to keep data")
):
    """
    Clean up old data for a user.
    
    Args:
        user_id: User identifier
        days_old: Number of days to keep data
    """
    try:
        cleanup_result = await email_service.cleanup_old_data(user_id, days_old)
        
        return {
            "success": True,
            "deleted_drafts": cleanup_result.get('deleted_drafts', 0),
            "deleted_sent_emails": cleanup_result.get('deleted_sent_emails', 0),
            "errors": cleanup_result.get('errors', [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up user data: {str(e)}")


@router.get("/providers")
async def get_supported_providers():
    """
    Get list of supported email providers.
    """
    return {
        "providers": [
            {
                "name": "google",
                "display_name": "Google Gmail",
                "description": "Connect your Gmail account"
            },
            {
                "name": "outlook",
                "display_name": "Microsoft Outlook",
                "description": "Connect your Outlook account"
            },
            {
                "name": "yahoo",
                "display_name": "Yahoo Mail",
                "description": "Connect your Yahoo Mail account"
            }
        ]
    }
