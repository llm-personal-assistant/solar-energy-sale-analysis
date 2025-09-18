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

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Initialize auth service lazily
auth_service = None

def get_auth_service():
    global auth_service
    if auth_service is None:
        auth_service = AuthService()
    return auth_service

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
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

@router.post("/signin", response_model=AuthResponse)
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

@router.post("/signout")
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

@router.get("/me", response_model=UserResponse)
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

@router.post("/refresh", response_model=TokenResponse)
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

@router.post("/reset-password")
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
        get_auth_service().supabase.auth.set_session(credentials.credentials, "")
        
        # Get current user
        user = await get_auth_service().get_current_user()
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

@router.get("/confirm")
async def confirm_email(
    request: Request,
    token: str = Query(None, description="Email confirmation token"),
    type: str = Query(None, description="Confirmation type"),
    redirect_to: str = Query(None, description="Redirect URL after confirmation")
):
    """
    Handle email confirmation from Supabase
    Supports both query parameters and URL fragments
    """
    try:
        # Check if we have query parameters
        if token and type:
            print(f"Email confirmation via query params:")
            print(f"  Token: {token[:20]}...")
            print(f"  Type: {type}")
            print(f"  Redirect to: {redirect_to}")
            
            # Process the confirmation
            return await process_email_confirmation(token, type, redirect_to)
        
        # If no query params, return a page that handles URL fragments
        return await handle_fragment_confirmation(request)
        
    except Exception as e:
        print(f"Unexpected error in email confirmation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

async def process_email_confirmation(token: str, type: str, redirect_to: str = None):
    """
    Process the actual email confirmation
    """
    try:
        # Use Supabase to verify the token
        response = get_auth_service().supabase.auth.verify_otp({
            "token": token,
            "type": type
        })
        
        if response.user:
            print(f"Email confirmed successfully for user: {response.user.email}")
            
            # Create a success page
            success_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Email Confirmed</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 600px;
                        margin: 50px auto;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        text-align: center;
                    }}
                    .success {{
                        color: #28a745;
                        font-size: 24px;
                        margin-bottom: 20px;
                    }}
                    .message {{
                        color: #333;
                        font-size: 16px;
                        margin-bottom: 30px;
                    }}
                    .button {{
                        background-color: #007bff;
                        color: white;
                        padding: 12px 24px;
                        text-decoration: none;
                        border-radius: 5px;
                        display: inline-block;
                        margin: 10px;
                    }}
                    .button:hover {{
                        background-color: #0056b3;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success">✅ Email Confirmed Successfully!</div>
                    <div class="message">
                        Your email <strong>{response.user.email}</strong> has been confirmed.
                        You can now sign in to your account.
                    </div>
                    <a href="/auth/signin" class="button">Sign In</a>
                    <a href="/" class="button">Go Home</a>
                </div>
            </body>
            </html>
            """
            
            return HTMLResponse(content=success_html, status_code=200)
        else:
            raise Exception("Invalid confirmation token")
            
    except Exception as e:
        print(f"Email confirmation failed: {e}")
        
        # Create an error page
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Email Confirmation Failed</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .error {{
                    color: #dc3545;
                    font-size: 24px;
                    margin-bottom: 20px;
                }}
                .message {{
                    color: #333;
                    font-size: 16px;
                    margin-bottom: 30px;
                }}
                .button {{
                    background-color: #007bff;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                    margin: 10px;
                }}
                .button:hover {{
                    background-color: #0056b3;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error">❌ Email Confirmation Failed</div>
                <div class="message">
                    The confirmation link is invalid or has expired.
                    <br><br>
                    Please try signing up again or contact support if the problem persists.
                </div>
                <a href="/auth/signup" class="button">Sign Up Again</a>
                <a href="/" class="button">Go Home</a>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=error_html, status_code=400)

async def handle_fragment_confirmation(request: Request):
    """
    Handle email confirmation with URL fragments (access_token, type, etc.)
    """
    fragment_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Email Confirmation</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            .loading {
                color: #007bff;
                font-size: 18px;
                margin-bottom: 20px;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #007bff;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 2s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .error {
                color: #dc3545;
                font-size: 18px;
                margin-bottom: 20px;
            }
            .button {
                background-color: #007bff;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 5px;
                display: inline-block;
                margin: 10px;
            }
            .button:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div id="loading" class="loading">
                <div class="spinner"></div>
                Processing email confirmation...
            </div>
            <div id="error" class="error" style="display: none;">
                Email confirmation failed. Please try again.
            </div>
            <div id="success" style="display: none;">
                <div style="color: #28a745; font-size: 24px; margin-bottom: 20px;">
                    ✅ Email Confirmed Successfully!
                </div>
                <div style="color: #333; font-size: 16px; margin-bottom: 30px;">
                    Your email has been confirmed. You can now sign in to your account.
                </div>
                <a href="/auth/signin" class="button">Sign In</a>
                <a href="/" class="button">Go Home</a>
            </div>
        </div>
        
        <script>
            // Parse URL fragments
            function parseFragment() {
                const hash = window.location.hash.substring(1);
                const params = new URLSearchParams(hash);
                
                const accessToken = params.get('access_token');
                const type = params.get('type');
                const expiresAt = params.get('expires_at');
                const refreshToken = params.get('refresh_token');
                
                console.log('Fragment params:', {
                    accessToken: accessToken ? accessToken.substring(0, 20) + '...' : null,
                    type: type,
                    expiresAt: expiresAt,
                    refreshToken: refreshToken ? refreshToken.substring(0, 10) + '...' : null
                });
                
                if (accessToken && type) {
                    // Send the confirmation to our backend
                    confirmEmail(accessToken, type);
                } else {
                    showError('Invalid confirmation link');
                }
            }
            
            async function confirmEmail(token, type) {
                try {
                    const response = await fetch(`/auth/confirm?token=${encodeURIComponent(token)}&type=${encodeURIComponent(type)}`);
                    
                    if (response.ok) {
                        // Get the HTML response and replace the current page
                        const html = await response.text();
                        document.body.innerHTML = html;
                    } else {
                        showError('Email confirmation failed');
                    }
                } catch (error) {
                    console.error('Confirmation error:', error);
                    showError('Email confirmation failed');
                }
            }
            
            function showError(message) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').textContent = message;
                document.getElementById('error').style.display = 'block';
            }
            
            // Run when page loads
            parseFragment();
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=fragment_html)

# Create FastAPI app for standalone running
app = FastAPI(
    title="Authentication API",
    description="Authentication service for email provider application",
    version="1.0.0"
)

# Include the auth router
app.include_router(router)

@app.get("/")
async def root():
    """Root endpoint with links to auth pages"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Email Provider Auth</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            h1 {
                color: #333;
                margin-bottom: 30px;
            }
            .button {
                background-color: #007bff;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 5px;
                display: inline-block;
                margin: 10px;
            }
            .button:hover {
                background-color: #0056b3;
            }
            .endpoints {
                text-align: left;
                margin-top: 30px;
                background: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Email Provider Authentication</h1>
            <p>Welcome to the email provider authentication system.</p>
            <a href="/auth/signup" class="button">Sign Up</a>
            <a href="/auth/signin" class="button">Sign In</a>
            <a href="/docs" class="button">API Docs</a>
            <a href="/health" class="button">Health Check</a>
            
            <div class="endpoints">
                <h3>Available Endpoints:</h3>
                <ul>
                    <li><strong>POST /auth/signup</strong> - Register new user</li>
                    <li><strong>POST /auth/signin</strong> - Sign in user</li>
                    <li><strong>POST /auth/signout</strong> - Sign out user</li>
                    <li><strong>GET /auth/me</strong> - Get current user</li>
                    <li><strong>POST /auth/refresh</strong> - Refresh token</li>
                    <li><strong>POST /auth/reset-password</strong> - Reset password</li>
                    <li><strong>GET /auth/confirm</strong> - Email confirmation</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/health")
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
    uvicorn.run(app, host="0.0.0.0", port=8001)
