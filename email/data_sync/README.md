# Email Data Sync Module

This module provides functionality for synchronizing email data with Supabase, including AI-analyzed lead information and associated email messages. It supports Gmail and Outlook email providers for reading and syncing emails.

## Overview

The data sync module manages two main tables in the `email` schema:

1. **`email_lead`** - Stores analyzed email lead information with AI insights
2. **`email_message`** - Stores individual email messages linked to leads

## Email Provider Support

- **Gmail** - Full support via Gmail API
- **Outlook** - Full support via Microsoft Graph API
- **Extensible** - Easy to add support for other email providers

## Database Schema

### Email Lead Table

The `email_lead` table stores comprehensive AI analysis of email leads including:

- **Basic Information**: lead_id, owner, subject, summary, internal_date
- **Intent Analysis**: category, confidence score, reasoning
- **Purchase Intent**: score (0-100), reasoning
- **Sentiment Analysis**: label (Positive/Neutral/Negative), score (-1 to 1), reasoning
- **Urgency Analysis**: level (High/Medium/Low), reasoning
- **Keywords & Pain Points**: arrays of extracted keywords and pain points
- **Sales Opportunities**: upsell/cross-sell value and reasoning
- **Discount Sensitivity**: level and reasoning
- **Recommendations**: priority level and recommended steps

### Email Message Table

The `email_message` table stores individual email messages with:

- **Basic Information**: message_id, lead_id (foreign key), owner, sender, receiver
- **Content**: subject, body, summary
- **Email Status**: is_read, folder (inbox, sent, drafts, etc.)
- **Metadata**: raw_data (JSONB), internal_date, history_id
- **Timestamps**: created_at, updated_at

## Features

### Data Models

- **Pydantic Models**: Type-safe data models with validation
- **Enums**: Predefined values for sentiment, urgency, priority, and discount sensitivity
- **Base/Create/Update Models**: Separate models for different operations

### Email Provider Services

#### Gmail Service
- **GmailService**: Handles Gmail API authentication and email retrieval
- **Features**: Read emails, get folders, mark as read, thread support
- **Authentication**: OAuth2 with access/refresh tokens

#### Outlook Service  
- **OutlookService**: Handles Microsoft Graph API authentication and email retrieval
- **Features**: Read emails, get folders, mark as read, conversation support
- **Authentication**: OAuth2 with access tokens

### Unified Sync Service

The `EmailSyncService` provides unified email synchronization:

#### Core Operations
- `sync_emails_for_user()` - Sync emails from all user accounts
- `sync_emails_for_account()` - Sync emails from specific account
- `get_user_messages()` - Retrieve user messages from database
- `get_sync_status()` - Get synchronization statistics

### Data Sync Service

The `EmailDataSyncService` provides comprehensive CRUD operations:

#### Lead Operations
- `create_lead()` - Create new email lead
- `get_lead()` - Retrieve lead by ID
- `update_lead()` - Update existing lead
- `delete_lead()` - Delete lead (cascades to messages)
- `list_leads()` - List leads with pagination
- `search_leads()` - Search leads by text content

#### Message Operations
- `create_message()` - Create new email message
- `get_message()` - Retrieve message by ID
- `update_message()` - Update existing message
- `delete_message()` - Delete message
- `get_messages_by_lead()` - Get all messages for a lead

#### Advanced Operations
- `get_lead_with_messages()` - Get lead with all associated messages
- `bulk_sync()` - Bulk synchronization of leads and messages
- `get_analytics()` - Get analytics and statistics

### Security Features

- **Row Level Security (RLS)**: Users can only access their own data
- **User ID Validation**: All operations require user authentication
- **Cascade Deletes**: Deleting a lead automatically deletes associated messages

### Performance Optimizations

- **Indexes**: Optimized indexes on frequently queried columns
- **Triggers**: Automatic `updated_at` timestamp updates
- **Pagination**: Built-in pagination for list operations

## Usage

### Basic Setup

```python
from data_sync import EmailSyncService, GmailService, OutlookService
from common.supabase_client import get_supabase_client

# Initialize services
supabase = get_supabase_client()
email_sync_service = EmailSyncService(supabase)
gmail_service = GmailService()
outlook_service = OutlookService()
```

### Gmail Integration

```python
# Authenticate with Gmail
gmail_service.authenticate_with_tokens(access_token, refresh_token)

# Get folders
folders = gmail_service.get_folders()
print(f"Available folders: {[f['name'] for f in folders]}")

# Get messages
messages = gmail_service.get_messages(folder_id='INBOX', max_results=10)
print(f"Retrieved {len(messages)} messages")
```

### Outlook Integration

```python
# Authenticate with Outlook
outlook_service.authenticate_with_token(access_token)

# Get folders
folders = outlook_service.get_folders()
print(f"Available folders: {[f['name'] for f in folders]}")

# Get messages
messages = outlook_service.get_messages(folder_id='inbox', max_results=10)
print(f"Retrieved {len(messages)} messages")
```

### Creating a Lead

```python
from data_sync import EmailLeadCreate, SentimentLabel, UrgencyLevel, PriorityLevel, DiscountSensitivityLevel

lead_data = EmailLeadCreate(
    lead_id="lead_123",
    owner="sales@company.com",
    subject="Interested in Solar Panels",
    intent_category="Product Inquiry",
    intent_confidence=0.85,
    intent_reason="Customer asked about pricing and installation",
    purchase_intent_score=75,
    purchase_intent_reason="High engagement and specific questions",
    sentiment_label=SentimentLabel.POSITIVE,
    sentiment_score=0.7,
    sentiment_reason="Enthusiastic tone and positive language",
    urgency_level=UrgencyLevel.MEDIUM,
    urgency_reason="Customer wants quote within week",
    pain_points=["High electricity bills", "Environmental concerns"],
    keywords=["solar", "panels", "installation", "cost"],
    upsell_value=True,
    upsell_reason="Customer has large property suitable for battery storage",
    cross_sell_value=False,
    cross_sell_reason=None,
    discount_sensitivity_level=DiscountSensitivityLevel.MEDIUM,
    discount_sensitivity_reason="Price-conscious but values quality",
    recommended_steps=["Send detailed quote", "Schedule site visit"],
    priority_level=PriorityLevel.HIGH
)

result = await sync_service.create_lead(lead_data, user_id)
```

### Creating a Message

```python
from data_sync import EmailMessageCreate

message_data = EmailMessageCreate(
    message_id="msg_456",
    lead_id="lead_123",
    owner="sales@company.com",
    sender="customer@email.com",
    receiver="sales@company.com",
    subject="Re: Solar Panel Quote Request",
    body="Thank you for the information. I'm very interested...",
    summary="Customer expressing strong interest and asking for next steps",
    internal_date=1640995200000,
    history_id=789
)

result = await sync_service.create_message(message_data, user_id)
```

### Email Synchronization

```python
from data_sync import EmailSyncRequest

# Sync emails for a user
sync_request = EmailSyncRequest(
    user_id="user_123",
    max_messages=100,
    folder="inbox"  # Optional: specific folder
)

result = await email_sync_service.sync_emails_for_user(sync_request)
print(f"Synced {result.messages_synced} messages")
print(f"Created {result.messages_created} new messages")
print(f"Updated {result.messages_updated} existing messages")
```

### Bulk Synchronization

```python
from data_sync import BulkSyncRequest

sync_request = BulkSyncRequest(
    leads=[lead_data1, lead_data2],
    messages=[message_data1, message_data2],
    user_id=user_id
)

stats = await sync_service.bulk_sync(sync_request)
print(f"Processed {stats.leads_processed} leads and {stats.messages_processed} messages")
```

### Analytics

```python
analytics = await sync_service.get_analytics(user_id)
print(f"Total leads: {analytics['total_leads']}")
print(f"Priority distribution: {analytics['priority_distribution']}")
print(f"Sentiment distribution: {analytics['sentiment_distribution']}")
```

## Database Setup

To set up the database tables, run the SQL schema file:

```sql
-- Execute the database_schema.sql file in your Supabase database
-- This will create the email schema and tables with proper indexes and RLS policies
```

## Error Handling

All service methods return `DataSyncResponse` objects with:
- `success`: Boolean indicating operation success
- `message`: Human-readable message
- `data`: Optional response data
- `errors`: List of error messages if any

## Dependencies

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Key dependencies include:
- `supabase-py`: Supabase client library
- `pydantic`: Data validation and serialization
- `google-api-python-client`: Gmail API client
- `requests`: HTTP client for Outlook API
- `python-dotenv`: Environment variable management

## Environment Variables

Make sure to set up the following environment variables:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Gmail API (optional)
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret

# Outlook API (optional)
OUTLOOK_CLIENT_ID=your_outlook_client_id
OUTLOOK_CLIENT_SECRET=your_outlook_client_secret
```

## API Setup

### Gmail API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download the credentials JSON file

### Outlook API Setup
1. Go to [Azure Portal](https://portal.azure.com/)
2. Register a new application
3. Add Microsoft Graph API permissions (Mail.Read, Mail.ReadWrite)
4. Generate client secret
5. Configure redirect URIs

## API Endpoints

The module provides REST API endpoints for email synchronization:

### Authentication

All API endpoints require JWT token authentication. Include the token in the Authorization header:

```
Authorization: Bearer your_jwt_token_here
```

The user ID is automatically extracted from the JWT token, so you don't need to pass it in requests.

### Core Endpoints

- `GET /data-sync/accounts` - Get user's email accounts
- `POST /data-sync/sync` - Sync emails for a user
- `POST /data-sync/sync/account/{account_id}` - Sync emails for specific account
- `GET /data-sync/status` - Get sync status for a user
- `GET /data-sync/messages` - Get user messages
- `PATCH /data-sync/messages/{message_id}/read` - Mark message as read
- `GET /data-sync/folders/{provider}` - Get available folders for provider

### Example API Usage

```python
import requests

# Set up headers with authentication token
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_jwt_token_here"
}

# Get user accounts
response = requests.get(
    "http://localhost:8000/data-sync/accounts",
    headers=headers,
    params={"active_only": True}
)
accounts = response.json()

# Sync emails
response = requests.post(
    "http://localhost:8000/data-sync/sync",
    headers=headers,
    json={
        "max_messages": 100,
        "folder": "inbox",
        "background_sync": False
    }
)
result = response.json()
```

## Examples

See `api_usage_example.py` for comprehensive examples of:
- REST API usage with Python client
- cURL command examples
- Gmail email synchronization
- Outlook email synchronization  
- Unified email sync service usage
- Database operations

## File Structure

```
data_sync/
├── __init__.py              # Module exports
├── models.py                # Pydantic data models
├── database_schema.sql      # Database schema
├── gmail_service.py         # Gmail API service
├── outlook_service.py       # Outlook API service
├── email_sync_service.py    # Unified sync service
├── sync_service.py          # Legacy data sync service
├── data_sync_routes.py      # REST API routes
├── requirements.txt         # Dependencies
├── api_usage_example.py     # API usage examples
└── README.md               # This file
```
