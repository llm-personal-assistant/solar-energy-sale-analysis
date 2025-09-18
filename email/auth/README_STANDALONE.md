# Standalone Authentication Server

The `routes.py` file can now be run as a standalone FastAPI application for testing and development purposes.

## Quick Start

### Option 1: Run directly from routes.py
```bash
cd auth
python routes.py
```

### Option 2: Use the helper script
```bash
# From the main email directory
python run_auth_server.py
```

### Option 3: Run with uvicorn directly
```bash
cd auth
uvicorn routes:app --host 0.0.0.0 --port 8001 --reload
```

## Server Information

- **URL**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **ReDoc Documentation**: http://localhost:8001/redoc

## Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with basic info |
| GET | `/health` | Health check endpoint |
| POST | `/auth/signup` | Register new user |
| POST | `/auth/signin` | Sign in user |
| POST | `/auth/signout` | Sign out user |
| GET | `/auth/me` | Get current user |
| POST | `/auth/refresh` | Refresh token |
| POST | `/auth/reset-password` | Reset password |

## Testing

Run the test script to verify the server is working:

```bash
# Terminal 1: Start the server
python run_auth_server.py

# Terminal 2: Run tests
python test_auth_server.py
```

## Environment Variables

Make sure these environment variables are set in your `.env` file in the `provider` directory:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Features

- ✅ **Standalone FastAPI App** - Can run independently
- ✅ **Auto-reload** - Automatically restarts on code changes
- ✅ **API Documentation** - Swagger UI and ReDoc included
- ✅ **Health Check** - Monitor server status
- ✅ **CORS Support** - Ready for frontend integration
- ✅ **Error Handling** - Comprehensive error responses

## Development

The server runs on port 8001 to avoid conflicts with the main email provider server (port 8000).

### Custom Configuration

You can modify the server configuration in `routes.py`:

```python
if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001, 
        reload=True,
        log_level="info"
    )
```

### Adding New Endpoints

Add new routes to the `router` object in `routes.py`:

```python
@router.get("/new-endpoint")
async def new_endpoint():
    return {"message": "New endpoint"}
```

The new endpoint will automatically be available at `/auth/new-endpoint` when the server is running.
