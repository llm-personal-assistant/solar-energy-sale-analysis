"""
Provider FastAPI Application

Main FastAPI application for the email provider service.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

# Import the provider router
from provider_routers import provider_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
provider_app = FastAPI(
    title="Email Provider Service API",
    description="Email provider service for OAuth authentication and account management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
provider_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
provider_app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure this properly for production
)


@provider_app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = datetime.now()
    
    # Log request
    logger.info(f"Provider Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Provider Response: {response.status_code} - {process_time:.3f}s")
    
    return response


@provider_app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Provider Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred in provider service",
            "timestamp": datetime.now().isoformat()
        }
    )


@provider_app.exception_handler(Exception)
async def http_exception_handler(request: Request, exc: Exception):
    """HTTP exception handler."""
    logger.warning(f"Provider HTTP exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Provider HTTP error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# Include the provider router
provider_app.include_router(provider_router, prefix="/api/v1")


@provider_app.get("/")
async def root():
    """Root endpoint with provider service information."""
    return {
        "message": "Email Provider Service API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "providers": "/api/v1/providers",
            "accounts": "/api/v1/providers/accounts",
            "oauth": "/api/v1/providers/{provider}/auth-url"
        }
    }


@provider_app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "email-provider-service"
    }


@provider_app.get("/api/v1/status")
async def api_status():
    """API status endpoint."""
    return {
        "api_version": "v1",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "service": "email-provider",
        "features": [
            "oauth_authentication",
            "multi_provider_support",
            "token_management",
            "account_management"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the provider application
    uvicorn.run(
        "provider_app:provider_app",
        host="0.0.0.0",
        port=8001,  # Different port from main email service
        reload=True,
        log_level="info"
    )
