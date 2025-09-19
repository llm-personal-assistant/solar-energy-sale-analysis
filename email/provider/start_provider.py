#!/usr/bin/env python3
"""
Provider Service Startup Script

This script starts the FastAPI provider service server.
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Start the provider service server."""
    
    # Configuration
    host = os.getenv("PROVIDER_HOST", "0.0.0.0")
    port = int(os.getenv("PROVIDER_PORT", 8001))
    reload = os.getenv("PROVIDER_RELOAD", "true").lower() == "true"
    log_level = os.getenv("PROVIDER_LOG_LEVEL", "info")
    
    print(f"Starting Email Provider Service API server...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Reload: {reload}")
    print(f"Log Level: {log_level}")
    print(f"Docs: http://{host}:{port}/docs")
    print(f"ReDoc: http://{host}:{port}/redoc")
    
    # Start the server
    uvicorn.run(
        "provider_app:provider_app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )

if __name__ == "__main__":
    main()
