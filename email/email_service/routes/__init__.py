"""
FastAPI Routes Package

This package contains all the API routes for the email service.
"""

from .email_routes import router as email_router
from .send_routes import router as send_router
from .draft_routes import router as draft_router
from .account_routes import router as account_router

__all__ = ['email_router', 'send_router', 'draft_router', 'account_router']
