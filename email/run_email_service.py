#!/usr/bin/env python3
"""
Email Service Runner

This script runs the email service from the correct directory to avoid import issues.
"""

import sys
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
try:
    from .email_service.routes import email_router, send_router, draft_router, account_router
except ImportError:
    from email_service.routes import email_router, send_router, draft_router, account_router

try:
    from .provider.provider_routes import provider_router
except ImportError:
    from provider.provider_routes import provider_router

try:
    from .auth.auth_routes import auth_router
except ImportError:
    from auth.auth_routes import auth_router

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


app = FastAPI(
    title="Email Provider API",
    description="API for managing email providers (Google, Outlook, Yahoo) with Supabase",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(provider_router)
app.include_router(auth_router)
app.include_router(email_router)
app.include_router(send_router)
app.include_router(draft_router)
app.include_router(account_router)  

# Import and run the FastAPI app
if __name__ == "__main__":
       uvicorn.run(app, host="0.0.0.0", port=8000)
