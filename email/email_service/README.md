# Email Service

A comprehensive email service that provides unified access to email reading, sending, and draft management functionality across multiple email providers (Google, Outlook, Yahoo).

## Features

- **Email Reading**: Read emails from connected accounts with automatic token refresh
- **Email Sending**: Send individual or bulk emails with rate limiting
- **Draft Management**: Create, update, delete, and send email drafts
- **Multi-Provider Support**: Works with Google Gmail, Microsoft Outlook, and Yahoo Mail
- **Search Functionality**: Search through emails and drafts
- **Statistics**: Get email statistics and account information
- **Data Cleanup**: Clean up old email data

## Architecture

The email service is organized into several modules:

- `EmailService`: Main service class that provides unified access to all operations
- `EmailReader`: Handles reading emails and managing read/unread status
- `EmailSender`: Handles sending emails and bulk operations
- `DraftManager`: Manages email drafts (create, update, delete, send)

## Installation

Make sure you have the required dependencies installed:

```bash
pip install httpx google-auth google-auth-oauthlib google-api-python-client msal
```

## Usage

### Basic Setup

```python
from email_service import EmailService

# Initialize the service
email_service = EmailService()

# Your user and account IDs (from your authentication system)
user_id = "user_123"
account_id = "account_456"
```

### Reading Emails

```python
# Get emails from an account
emails = await email_service.get_emails(user_id, account_id, limit=50)

# Get only unread emails
unread_emails = await email_service.get_emails(
    user_id, account_id, limit=50, unread_only=True
)

# Get emails since a specific date
from datetime import datetime, timezone
since_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
recent_emails = await email_service.get_emails(
    user_id, account_id, since_date=since_date
)

# Search emails
search_results = await email_service.search_emails(
    user_id, account_id, "important", limit=10
)

# Mark email as read/unread
await email_service.mark_as_read(user_id, account_id, message_id)
await email_service.mark_as_unread(user_id, account_id, message_id)
```

### Sending Emails

```python
# Send a simple email
result = await email_service.send_email(
    user_id=user_id,
    account_id=account_id,
    to_emails=["recipient@example.com"],
    subject="Hello World",
    body="This is a test email.",
    is_html=False
)

# Send HTML email with CC and BCC
result = await email_service.send_email(
    user_id=user_id,
    account_id=account_id,
    to_emails=["recipient@example.com"],
    subject="HTML Email",
    body="<h1>Hello</h1><p>This is an HTML email.</p>",
    is_html=True,
    cc_emails=["cc@example.com"],
    bcc_emails=["bcc@example.com"]
)

# Send bulk emails
email_list = [
    {
        "to_emails": ["user1@example.com"],
        "subject": "Bulk Email 1",
        "body": "Content 1"
    },
    {
        "to_emails": ["user2@example.com"],
        "subject": "Bulk Email 2",
        "body": "Content 2"
    }
]

bulk_result = await email_service.send_bulk_email(
    user_id, account_id, email_list, batch_size=5
)
```

### Draft Management

```python
# Create a draft
draft_result = await email_service.create_draft(
    user_id=user_id,
    account_id=account_id,
    to_emails=["recipient@example.com"],
    subject="Draft Email",
    body="This is a draft email.",
    is_html=False
)

if draft_result['success']:
    draft_id = draft_result['draft_id']
    
    # Update the draft
    await email_service.update_draft(
        user_id, draft_id,
        subject="Updated Draft Email",
        body="This is an updated draft email."
    )
    
    # Send the draft
    send_result = await email_service.send_draft(user_id, draft_id)
    
    # Or delete the draft
    await email_service.delete_draft(user_id, draft_id)

# Get all drafts
drafts = await email_service.get_user_drafts(user_id, limit=20)

# Search drafts
search_results = await email_service.search_drafts(
    user_id, "meeting", limit=10
)
```

### Account Management

```python
# Get all email accounts for a user
accounts = await email_service.get_user_accounts(user_id)

# Get OAuth URL for connecting a new account
auth_url = await email_service.get_auth_url("google", user_id)

# Handle OAuth callback (typically in your web application)
account = await email_service.handle_oauth_callback(
    user_id, "google", authorization_code
)
```

### Statistics and Cleanup

```python
# Get email statistics
stats = await email_service.get_email_statistics(user_id)
print(f"Total emails: {stats['total_emails']}")
print(f"Unread emails: {stats['unread_emails']}")
print(f"Sent emails: {stats['sent_emails']}")
print(f"Drafts: {stats['drafts']}")

# Clean up old data (older than 30 days)
cleanup_result = await email_service.cleanup_old_data(user_id, days_old=30)
```

## Database Schema

The service expects the following database tables in the `email_provider` schema:

### email_accounts
- `id`: Primary key
- `user_id`: User identifier
- `email`: Email address
- `provider`: Provider name (google, outlook, yahoo)
- `access_token`: OAuth access token
- `refresh_token`: OAuth refresh token
- `is_active`: Boolean flag
- `created_at`: Timestamp
- `updated_at`: Timestamp

### email_messages
- `id`: Primary key
- `account_id`: Foreign key to email_accounts
- `message_id`: Provider message ID
- `subject`: Email subject
- `sender`: Sender email
- `recipient`: Recipient email
- `body`: Email body
- `timestamp`: Email timestamp
- `is_read`: Boolean flag
- `created_at`: Timestamp

### email_drafts
- `id`: Primary key
- `user_id`: User identifier
- `account_id`: Foreign key to email_accounts
- `to_emails`: JSON array of recipient emails
- `subject`: Email subject
- `body`: Email body
- `is_html`: Boolean flag
- `cc_emails`: JSON array of CC emails
- `bcc_emails`: JSON array of BCC emails
- `attachments`: JSON array of attachments
- `status`: Draft status (draft, sent)
- `created_at`: Timestamp
- `updated_at`: Timestamp
- `sent_at`: Timestamp (when sent)

### sent_emails
- `id`: Primary key
- `user_id`: User identifier
- `account_id`: Foreign key to email_accounts
- `message_id`: Provider message ID
- `subject`: Email subject
- `recipients`: Comma-separated recipient emails
- `cc_recipients`: Comma-separated CC emails
- `bcc_recipients`: Comma-separated BCC emails
- `body_preview`: Email body preview
- `sent_at`: Timestamp
- `status`: Send status

### oauth_states
- `id`: Primary key
- `state`: OAuth state parameter
- `provider`: Provider name
- `user_id`: User identifier
- `expires_at`: Expiration timestamp
- `verified`: Boolean flag
- `verified_at`: Verification timestamp

## Error Handling

All methods return dictionaries with success/error information:

```python
result = await email_service.send_email(...)

if result['success']:
    print(f"Email sent: {result['message_id']}")
else:
    print(f"Error: {result['error']}")
```

## Token Management

The service automatically handles OAuth token refresh for Google accounts. For other providers, you may need to implement additional refresh logic.

## Rate Limiting

Bulk email sending includes built-in rate limiting with configurable batch sizes and delays between batches.

## Security

- All tokens are stored securely in the database
- OAuth states are validated and have expiration times
- User access is verified for all operations
- Sensitive data is not logged

## Example

See `example_usage.py` for a complete example of how to use the EmailService.
