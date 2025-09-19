# Email Service

This service provides core email functionality including sending emails, reading emails, and managing draft emails.

## Features

- **Email Sending**: Send emails through multiple providers (Google, Outlook)
- **Email Reading**: Retrieve and read emails from connected accounts
- **Draft Management**: Save, update, delete, and send draft emails
- **Multi-Provider Support**: Google Gmail, Microsoft Outlook

## API Endpoints

### Email Accounts
- `GET /email/email-accounts` - Get all email accounts for user

### Email Operations
- `GET /email/emails/{account_id}` - Get emails from specific account
- `POST /email/send-email/{account_id}` - Send email using specific account

### Draft Management
- `POST /email/save-draft/{account_id}` - Save email as draft
- `GET /email/drafts` - Get all draft emails
- `GET /email/drafts/{draft_id}` - Get specific draft
- `PUT /email/drafts/{draft_id}` - Update draft
- `DELETE /email/drafts/{draft_id}` - Delete draft
- `POST /email/send-draft/{draft_id}/{account_id}` - Send draft email

## Database Schema

The service uses the following tables in the `email_provider` schema:

- `email_accounts` - User email account configurations
- `email_messages` - Received email messages
- `draft_emails` - Draft email storage

## Environment Variables

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Google OAuth (for token refresh)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

## Running the Service

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python service_routes.py
```

The service will be available at `http://localhost:8001`
