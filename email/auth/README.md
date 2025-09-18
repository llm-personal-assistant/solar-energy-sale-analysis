# Authentication Module

This module provides authentication functionality for the email provider application using Supabase Auth.

## Features

- **User Registration**: Sign up with email and password
- **User Login**: Sign in with email and password  
- **User Logout**: Sign out current user
- **Token Management**: Access and refresh token handling
- **Password Reset**: Send password reset emails
- **Current User**: Get current authenticated user

## API Endpoints

### Authentication Routes (`/auth`)

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| POST | `/auth/signup` | Register new user | `UserSignUp` | `AuthResponse` |
| POST | `/auth/signin` | Sign in user | `UserSignIn` | `AuthResponse` |
| POST | `/auth/signout` | Sign out user | None | `{message: string}` |
| GET | `/auth/me` | Get current user | None | `UserResponse` |
| POST | `/auth/refresh` | Refresh token | `refresh_token: string` | `TokenResponse` |
| POST | `/auth/reset-password` | Reset password | `email: string` | `{message: string}` |

## Models

### UserSignUp
```python
{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"  # Optional
}
```

### UserSignIn
```python
{
    "email": "user@example.com", 
    "password": "securepassword"
}
```

### AuthResponse
```python
{
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "full_name": "John Doe",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    },
    "access_token": "jwt_token",
    "refresh_token": "refresh_token"
}
```

## Usage

### Basic Authentication Flow

1. **Register a new user**:
```python
from auth import AuthService, UserSignUp

auth_service = AuthService()
user_data = UserSignUp(
    email="user@example.com",
    password="securepassword",
    full_name="John Doe"
)
result = await auth_service.sign_up(user_data)
```

2. **Sign in existing user**:
```python
from auth import UserSignIn

credentials = UserSignIn(
    email="user@example.com",
    password="securepassword"
)
result = await auth_service.sign_in(credentials)
```

3. **Get current user**:
```python
current_user = await auth_service.get_current_user()
```

4. **Sign out**:
```python
await auth_service.sign_out()
```

### Using with FastAPI

The authentication routes are automatically included when you import and use the auth router:

```python
from fastapi import FastAPI
from auth import auth_router

app = FastAPI()
app.include_router(auth_router)
```

### Protecting Routes

Use the `get_current_user_from_token` dependency to protect routes:

```python
from fastapi import Depends
from auth import get_current_user_from_token

@app.get("/protected")
async def protected_route(current_user = Depends(get_current_user_from_token)):
    return {"user_id": current_user.id, "email": current_user.email}
```

## Testing

Run the test script to verify authentication functionality:

```bash
cd auth
python test_auth.py
```

## Environment Variables

Make sure these environment variables are set in your `.env` file:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Error Handling

The authentication service includes comprehensive error handling:

- **400 Bad Request**: Invalid input data or validation errors
- **401 Unauthorized**: Invalid credentials or expired tokens
- **500 Internal Server Error**: Server-side errors

All errors include descriptive messages to help with debugging.
