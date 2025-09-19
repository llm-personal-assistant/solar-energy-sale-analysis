from fastapi import APIRouter, HTTPException, Depends, status, FastAPI, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from typing import Optional
import uvicorn

# Handle both relative and absolute imports
try:
    from .models import UserSignUp, UserSignIn, AuthResponse, UserResponse, TokenResponse
    from .auth_service import AuthService
except ImportError:
    from models import UserSignUp, UserSignIn, AuthResponse, UserResponse, TokenResponse
    from auth_service import AuthService

auth_router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Initialize auth service lazily
auth_service = None

def get_auth_service():
    global auth_service
    if auth_service is None:
        auth_service = AuthService()
    return auth_service

@auth_router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(user_data: UserSignUp):
    """
    Sign up a new user with email and password
    """
    try:
        print(f"Signing up user: {user_data}")
        result = await get_auth_service().sign_up(user_data)
        print(f"Signed up user: {result}")
        
        # Check if email confirmation is required
        if not result.access_token:
            print("Email confirmation required - returning user info without session")
            # Return a custom response indicating email confirmation is needed
            return {
                "user": result.user,
                "access_token": "",
                "refresh_token": "",
                "message": "User created successfully. Please check your email to confirm your account before signing in.",
                "email_confirmation_required": True
            }
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.post("/signin", response_model=AuthResponse)
async def sign_in(credentials: UserSignIn):
    """
    Sign in user with email and password
    """
    try:
        result = await get_auth_service().sign_in(credentials)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.post("/signout")
async def sign_out():
    """
    Sign out the current user
    """
    try:
        success = await get_auth_service().sign_out()
        if success:
            return {"message": "Successfully signed out"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to sign out"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user():
    """
    Get the current authenticated user
    """
    try:
        user = await get_auth_service().get_current_user()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """
    Refresh the access token using refresh token
    """
    try:
        result = await get_auth_service().refresh_token(refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.post("/reset-password")
async def reset_password(email: str):
    """
    Send password reset email
    """
    try:
        success = await get_auth_service().reset_password(email)
        if success:
            return {"message": "Password reset email sent"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to send password reset email"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Dependency to get current user from token
async def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """
    Dependency to extract and validate user from JWT token
    """
    try:
        # Set the session with the provided token
        access_token = credentials.credentials
        # Get current user
        user = await get_auth_service().get_current_user(jwt=access_token)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# @router.get("/confirm")
# async def confirm_email(
#     request: Request,
#     token: str = Query(None, description="Email confirmation token"),
#     type: str = Query(None, description="Confirmation type"),
#     redirect_to: str = Query(None, description="Redirect URL after confirmation")
# ):
#     """
#     Handle email confirmation from Supabase
#     Supports both query parameters and URL fragments
#     """
#     try:
#         # Check if we have query parameters
#         if token and type:
#             print(f"Email confirmation via query params:")
#             print(f"  Token: {token[:20]}...")
#             print(f"  Type: {type}")
#             print(f"  Redirect to: {redirect_to}")
            
#             # Process the confirmation
#             return await process_email_confirmation(token, type, redirect_to)
        
#         # If no query params, return a page that handles URL fragments
#         return await handle_fragment_confirmation(request)
        
#     except Exception as e:
#         print(f"Unexpected error in email confirmation: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error"
#         )


# Create FastAPI app for standalone running
auth_app = FastAPI(
    title="Authentication API",
    description="Authentication service for email provider application",
    version="1.0.0"
)

# Include the auth router
auth_app.include_router(auth_router)


@auth_app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "authentication"}

if __name__ == "__main__":
    import uvicorn
    print("Starting Authentication API Server...")
    print("=" * 50)
    print("Server will be available at: http://localhost:8001")
    print("API Documentation at: http://localhost:8001/docs")
    print("Email Confirmation at: http://localhost:8001/auth/confirm")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    uvicorn.run(auth_app, host="0.0.0.0", port=8001)
