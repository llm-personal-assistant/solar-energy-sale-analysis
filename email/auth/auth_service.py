import os
import sys
import uvicorn
from typing import Optional, Dict, Any
from supabase import Client

# Add the parent directory to the path to access provider module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from provider.supabase_client import get_supabase_client

# Handle both relative and absolute imports
try:
    from .models import UserSignUp, UserSignIn, AuthResponse, UserResponse, TokenResponse
except ImportError:
    from models import UserSignUp, UserSignIn, AuthResponse, UserResponse, TokenResponse

class AuthService:
    def __init__(self):
        self.supabase: Client = get_supabase_client().get_client()
    
    async def sign_up(self, user_data: UserSignUp) -> AuthResponse:
        """
        Sign up a new user with email and password
        """
        try:
            # Sign up user with Supabase Auth
            print(f"Signing up user with Supabase Auth: {user_data}")
            auth_response = self.supabase.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {
                    "data": {
                        "full_name": user_data.full_name
                    },
                    "email_redirect_to": "http://localhost:8001/auth/confirm"  # Redirect to auth confirmation endpoint
                }
            })
            print(f"Auth response: {auth_response}")
            
            if auth_response.user is None:
                raise ValueError("Failed to create user account")
            
            # Get user data
            user = auth_response.user
            print(f"User: {user}")
            session = auth_response.session
            print(f"Session: {session}")
            
            # Handle case where session is None (email confirmation required)
            if session is None:
                print("Session is None - this usually means email confirmation is required")
                print("User created but needs to confirm email before getting session")
                
                # Return a response indicating email confirmation is needed
                user_response = UserResponse(
                    id=user.id,
                    email=user.email,
                    full_name=user.user_metadata.get('full_name'),
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
                
                return AuthResponse(
                    user=user_response,
                    access_token="",  # Empty token since session is not available
                    refresh_token=""  # Empty refresh token
                )
            
            # Create user response for successful signup with session
            user_response = UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.user_metadata.get('full_name'),
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            print(f"User response: {user_response}")
            return AuthResponse(
                user=user_response,
                access_token=session.access_token,
                refresh_token=session.refresh_token
            )
            
        except Exception as e:
            print(f"Sign up error: {str(e)}")
            raise ValueError(f"Sign up failed: {str(e)}")
    
    async def sign_in(self, credentials: UserSignIn) -> AuthResponse:
        """
        Sign in user with email and password
        """
        try:
            # Sign in user with Supabase Auth
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": credentials.email,
                "password": credentials.password
            })
            
            if auth_response.user is None or auth_response.session is None:
                raise ValueError("Invalid email or password")
            
            # Get user data
            user = auth_response.user
            session = auth_response.session
            
            # Create user response
            user_response = UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.user_metadata.get('full_name'),
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
            return AuthResponse(
                user=user_response,
                access_token=session.access_token,
                refresh_token=session.refresh_token
            )
            
        except Exception as e:
            raise ValueError(f"Sign in failed: {str(e)}")
    
    async def sign_out(self) -> bool:
        """
        Sign out the current user
        """
        try:
            # Sign out user
            self.supabase.auth.sign_out()
            return True
        except Exception as e:
            print(f"Sign out failed: {str(e)}")
            return False
    
    async def get_current_user(self) -> Optional[UserResponse]:
        """
        Get the current authenticated user
        """
        try:
            # Get current user
            user = self.supabase.auth.get_user()
            
            if user.user is None:
                return None
            
            return UserResponse(
                id=user.user.id,
                email=user.user.email,
                full_name=user.user.user_metadata.get('full_name'),
                created_at=user.user.created_at,
                updated_at=user.user.updated_at
            )
            
        except Exception as e:
            print(f"Failed to get current user: {str(e)}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh the access token using refresh token
        """
        try:
            # Refresh token
            auth_response = self.supabase.auth.refresh_session(refresh_token)
            
            if auth_response.session is None:
                raise ValueError("Failed to refresh token")
            
            session = auth_response.session
            
            return TokenResponse(
                access_token=session.access_token,
                refresh_token=session.refresh_token
            )
            
        except Exception as e:
            raise ValueError(f"Token refresh failed: {str(e)}")
    
    async def reset_password(self, email: str) -> bool:
        """
        Send password reset email
        """
        try:
            # Send password reset email
            self.supabase.auth.reset_password_email(email)
            return True
        except Exception as e:
            print(f"Password reset failed: {str(e)}")
            return False
