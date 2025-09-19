# Common Utilities

This directory contains shared utilities and components used across multiple email services.

## Contents

### supabase_client.py
Shared Supabase client implementation used by both:
- **Provider Service**: For managing email accounts and OAuth states
- **Email Service**: For managing email messages and drafts

## Usage

### Import in Provider Service
```python
from common.supabase_client import get_supabase_client

# Get regular client
client = get_supabase_client().get_client()

# Get admin client (for service role operations)
admin_client = get_supabase_client().get_admin_client()
```

### Import in Email Service
```python
from common.supabase_client import get_supabase_client

# Get regular client
client = get_supabase_client().get_client()

# Get admin client (for service role operations)
admin_client = get_supabase_client().get_admin_client()
```

## Environment Variables

The Supabase client requires the following environment variables:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

## Features

- **Singleton Pattern**: Global instance ensures consistent client usage
- **Automatic Environment Loading**: Loads environment variables from .env file
- **Dual Client Support**: Provides both regular and admin clients
- **Error Handling**: Graceful handling of missing environment variables
- **Type Hints**: Full type annotation support

## Architecture

The common directory follows the shared library pattern:
- **Centralized Configuration**: Single source of truth for Supabase configuration
- **Consistent Interface**: Same API across all services
- **Easy Maintenance**: Updates to client logic affect all services
- **Reduced Duplication**: Eliminates code duplication across services
