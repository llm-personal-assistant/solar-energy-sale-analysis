import os
import sys
import uvicorn
import requests
from typing import Optional, Dict, Any
from supabase import Client

# Add the parent directory to the path to access provider module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from common.supabase_client import get_supabase_client
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from common.supabase_client import get_supabase_client

from dotenv import load_dotenv

load_dotenv()

# Handle both relative and absolute imports
try:
    from .models import UserSignUp, UserSignIn, AuthResponse, UserResponse, TokenResponse
except ImportError:
    from models import UserSignUp, UserSignIn, AuthResponse, UserResponse, TokenResponse

class AuthService:
    def __init__(self):
        self.supabase: Client = get_supabase_client().get_client()
        # Optional admin (service-role) client for privileged checks
        try:
            self.admin = get_supabase_client().get_admin_client()
        except Exception:
            self.admin = None
    
    def _build_user_response(self, user) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.user_metadata.get('full_name') if getattr(user, 'user_metadata', None) else None,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    def _auth_to_response(self, auth_obj) -> AuthResponse:
        user_response = self._build_user_response(auth_obj.user)
        session = getattr(auth_obj, 'session', None)
        if not session:
            return AuthResponse(user=user_response, access_token="", refresh_token="")
        return AuthResponse(user=user_response, access_token=session.access_token, refresh_token=session.refresh_token)
    
    def _try_sign_in(self, email: str, password: str) -> Optional[AuthResponse]:
        try:
            signin = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if signin.user and signin.session:
                return self._auth_to_response(signin)
        except Exception as e:
            print(f"Sign-in attempt failed: {e}")
        return None
    
    def _resend_confirmation(self, email: str) -> None:
        try:
            self.supabase.auth.resend({
                "type": "signup",
                "email": email
            })
        except Exception as e:
            print(f"Resend confirmation failed: {e}")
    
    def _get_user_by_email(self, email: str):
        url = f"{os.getenv('SUPABASE_URL')}/auth/v1/admin/users"
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        headers = {
        "apikey": service_key,  
        "Authorization": f"Bearer {service_key}"
         }
        resp = requests.get(url, headers=headers, params={"email": email})
        if resp.status_code == 200:
            data = resp.json()
            return data.get("users", [])[0] if data.get("users") else None
        else:
            raise Exception(f"Admin API failed: {resp.text}")
        
    async def sign_up(self, user_data: UserSignUp) -> AuthResponse:
        """
        Sign up a new user with email and password
        """
        try:
            # Pre-check existence via admin (if available)
            user = self._get_user_by_email(user_data.email)
            if user:
                # If exists, try sign-in; else resend confirmation and inform client
                return self._build_user_response
            
            # Proceed with signup
            auth_response = self.supabase.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {
                    "data": {
                        "full_name": user_data.full_name
                    }
                }
            })
            if auth_response.user is None:
                raise ValueError("Failed to create user account")
            
            return self._auth_to_response(auth_response)
        
        except Exception as e:
            raise ValueError(f"Sign up failed: {e}")
    
    async def confirm_email(self, token: str, type: str) -> AuthResponse:
        """
        Confirm email using verification token and return session tokens if available.
        """
        try:
            response = self.supabase.auth.verify_otp({
                "token": token,
                "type": type
            })
            if response.user is None:
                raise ValueError("Invalid or expired confirmation token")
            return self._auth_to_response(response)
        except Exception as e:
            raise ValueError(f"Email confirmation failed: {str(e)}")
    
    async def sign_in(self, credentials: UserSignIn) -> AuthResponse:
        """
        Sign in user with email and password
        """
        try:
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": credentials.email,
                "password": credentials.password
            })
            if auth_response.user is None or auth_response.session is None:
                raise ValueError("Invalid email or password")
            return self._auth_to_response(auth_response)
        except Exception as e:
            raise ValueError(f"Sign in failed: {str(e)}")
    
    async def sign_out(self) -> bool:
        """
        Sign out the current user
        """
        try:
            self.supabase.auth.sign_out()
            return True
        except Exception as e:
            print(f"Sign out failed: {str(e)}")
            return False
    
    async def get_current_user(self, jwt: str) -> Optional[UserResponse]:
        """
        Get the current authenticated user
        """
        try:
            user = self.supabase.auth.get_user(jwt=jwt)
            print(f"useruseruseruseruser {user}")
            if user.user is None:
                return None
            return self._build_user_response(user.user)
        except Exception as e:
            print(f"Failed to get current user: {str(e)}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh the access token using refresh token
        """
        try:
            auth_response = self.supabase.auth.refresh_session(refresh_token)
            if auth_response.session is None:
                raise ValueError("Failed to refresh token")
            session = auth_response.session
            return TokenResponse(access_token=session.access_token, refresh_token=session.refresh_token)
        except Exception as e:
            raise ValueError(f"Token refresh failed: {str(e)}")
    
    async def reset_password(self, email: str) -> bool:
        """
        Send password reset email
        """
        try:
            self.supabase.auth.reset_password_email(email)
            return True
        except Exception as e:
            print(f"Password reset failed: {str(e)}")
            return False
