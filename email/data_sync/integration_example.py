"""
Integration example showing how to add data sync routes to your FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the data sync router
from .data_sync_routes import router as data_sync_router

# Create FastAPI app
app = FastAPI(
    title="Email Data Sync API",
    description="API for synchronizing emails from Gmail and Outlook",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the data sync router
app.include_router(data_sync_router)

# Optional: Add other routers
# from auth.auth_routes import router as auth_router
# from provider.provider_routes import router as provider_router
# app.include_router(auth_router)
# app.include_router(provider_router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Email Data Sync API",
        "version": "1.0.0",
        "endpoints": {
            "data_sync": "/data-sync",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "email-data-sync-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
