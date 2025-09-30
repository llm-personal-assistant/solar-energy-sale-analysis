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
    from .email_service.service_routes import service_router
    from .provider.provider_routes import provider_router
    from .auth.auth_routes import auth_router
    from .data_sync.data_sync_routes import data_sync_router
    from .llm.llm_routes import llm_router
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from email_service.service_routes import service_router
    from provider.provider_routes import provider_router
    from auth.auth_routes import auth_router
    from data_sync.data_sync_routes import data_sync_router
    from llm.llm_routes import llm_router
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
app.include_router(service_router)
app.include_router(data_sync_router)
app.include_router(llm_router)

# Import and run the FastAPI app
if __name__ == "__main__":
       uvicorn.run(app, host="0.0.0.0", port=8000)
