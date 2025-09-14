# Email Provider API with Supabase

A FastAPI application that integrates with Supabase to provide email provider functionality for Google, Outlook, and Yahoo. Users can register their email accounts and read/send emails through the API.

## Features

- **Multi-Provider Support**: Google Gmail, Microsoft Outlook, and Yahoo Mail
- **OAuth Integration**: Secure authentication with all three providers
- **Email Operations**: Read and send emails through the API
- **Supabase Integration**: User management and data storage
- **Row Level Security**: Secure data access with RLS policies

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `env.example` to `.env` and fill in your credentials:

```bash
cp env.example .env
```

### 3. Supabase Setup

1. Create a new Supabase project
2. Run the SQL schema from `database_schema.sql` in your Supabase SQL editor
3. Get your project URL and anon key from the Supabase dashboard

### 4. OAuth Provider Setup

#### Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Add your redirect URI: `http://localhost:8000/oauth-callback/google`

#### Microsoft Outlook OAuth
1. Go to [Azure Portal](https://portal.azure.com/)
2. Register a new application
3. Add API permissions for Mail.Read and Mail.Send
4. Create a client secret
5. Add redirect URI: `http://localhost:8000/oauth-callback/outlook`

#### Yahoo OAuth
1. Go to [Yahoo Developer Network](https://developer.yahoo.com/)
2. Create a new application
3. Configure OAuth settings
4. Add redirect URI: `http://localhost:8000/oauth-callback/yahoo`

### 5. Run the Application

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication
- `GET /auth-url/{provider}` - Get OAuth URL for provider authentication
- `POST /oauth-callback/{provider}` - Handle OAuth callback

### Email Accounts
- `POST /register-email-provider` - Register a new email provider
- `GET /email-accounts` - Get user's email accounts

### Email Operations
- `GET /emails/{account_id}` - Get emails from an account
- `POST /send-email/{account_id}` - Send email using an account

## Usage Examples

### 1. Get OAuth URL for Google

```bash
curl -X GET "http://localhost:8000/auth-url/google" \
  -H "Authorization: Bearer YOUR_SUPABASE_JWT_TOKEN"
```

### 2. Register Email Account (after OAuth)

```bash
curl -X POST "http://localhost:8000/register-email-provider" \
  -H "Authorization: Bearer YOUR_SUPABASE_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@gmail.com",
    "provider": "google",
    "access_token": "oauth_access_token",
    "refresh_token": "oauth_refresh_token"
  }'
```

### 3. Get Emails

```bash
curl -X GET "http://localhost:8000/emails/ACCOUNT_ID?limit=10" \
  -H "Authorization: Bearer YOUR_SUPABASE_JWT_TOKEN"
```

### 4. Send Email

```bash
curl -X POST "http://localhost:8000/send-email/ACCOUNT_ID" \
  -H "Authorization: Bearer YOUR_SUPABASE_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["recipient@example.com"],
    "subject": "Test Email",
    "body": "This is a test email",
    "is_html": false
  }'
```

## Database Schema

The application uses the following main tables:

- `profiles` - User profile information
- `email_accounts` - Registered email accounts
- `email_messages` - Cached email messages
- `oauth_states` - OAuth flow state management

## Security Features

- Row Level Security (RLS) policies ensure users can only access their own data
- JWT token validation for all endpoints
- Secure OAuth flow with state parameter
- Automatic cleanup of expired OAuth states

## Development

### Project Structure

```
.
├── main.py                 # FastAPI application
├── supabase_client.py      # Supabase client configuration
├── auth.py                 # Authentication utilities
├── models.py               # Pydantic models
├── email_providers.py      # Email provider implementations
├── database_schema.sql     # Database schema
├── requirements.txt        # Python dependencies
├── env.example            # Environment variables template
└── README.md              # This file
```

### Adding New Email Providers

1. Create a new provider class in `email_providers.py`
2. Implement the required methods: `get_auth_url`, `exchange_code_for_tokens`, `get_emails`, `send_email`
3. Add the provider to the `EmailProviderManager` class
4. Update the database schema if needed

## Troubleshooting

### Common Issues

1. **OAuth Redirect URI Mismatch**: Ensure redirect URIs match exactly in OAuth provider settings
2. **Token Expiration**: Implement token refresh logic for long-running applications
3. **Rate Limiting**: Email providers have rate limits; implement proper error handling
4. **Yahoo API Limitations**: Yahoo Mail API has limited functionality; consider using IMAP/SMTP

### Debug Mode

Set `DEBUG=True` in your `.env` file for detailed error messages.

## License

This project is open source and available under the MIT License.
