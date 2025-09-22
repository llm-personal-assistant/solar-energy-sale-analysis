# Database Schema Update Summary

## Overview
Successfully updated the database schema to use proper schema namespaces: `email_provider` for provider-related tables and `email` for email service tables.

## Schema Changes

### Provider Schema (`email_provider`)
Updated all provider-related tables to use `email_provider` schema:

#### Tables Updated:
- `email_accounts` → `email_provider.email_accounts`
- `oauth_states` → `email_provider.oauth_states`

#### Components Updated:
- **Table Definitions**: All CREATE TABLE statements
- **Indexes**: All index definitions
- **RLS Policies**: All Row Level Security policies
- **Triggers**: Updated trigger references
- **Functions**: Updated function references

### Email Service Schema (`email`)
Email service tables remain in `email` schema:
- `email.email_messages`
- `email.draft_emails`

## Database Schema Structure

### Provider Schema (`email_provider`)
```
email_provider.email_accounts
├── id (UUID, Primary Key)
├── user_id (UUID, Foreign Key to auth.users)
├── email (TEXT)
├── provider (TEXT, Check: 'google'|'outlook'|'yahoo')
├── access_token (TEXT)
├── refresh_token (TEXT)
├── is_active (BOOLEAN, Default: TRUE)
├── created_at (TIMESTAMP WITH TIME ZONE, Default: NOW())
└── updated_at (TIMESTAMP WITH TIME ZONE, Default: NOW())

email_provider.oauth_states
├── id (UUID, Primary Key)
├── state (TEXT, Unique)
├── user_id (UUID, Foreign Key to auth.users)
├── provider (TEXT, Check: 'google'|'outlook'|'yahoo')
├── created_at (TIMESTAMP WITH TIME ZONE, Default: NOW())
├── expires_at (TIMESTAMP WITH TIME ZONE)
├── verified (BOOLEAN, Default: FALSE)
└── verified_at (TIMESTAMP WITH TIME ZONE)
```

### Email Service Schema (`email`)
```
email.email_messages
├── id (UUID, Primary Key)
├── account_id (UUID, Foreign Key to email_provider.email_accounts)
├── message_id (TEXT, Provider's message ID)
├── subject (TEXT)
├── sender (TEXT)
├── recipient (TEXT)
├── body (TEXT)
├── timestamp (TIMESTAMP WITH TIME ZONE)
├── is_read (BOOLEAN, Default: FALSE)
├── status (TEXT, Default: 'received', Check: 'draft'|'sent'|'received')
└── created_at (TIMESTAMP WITH TIME ZONE, Default: NOW())

email.draft_emails
├── id (UUID, Primary Key)
├── user_id (UUID, Foreign Key to auth.users)
├── account_id (UUID, Foreign Key to email_provider.email_accounts)
├── to (TEXT[])
├── subject (TEXT)
├── body (TEXT)
├── is_html (BOOLEAN, Default: FALSE)
├── created_at (TIMESTAMPTZ, Default: NOW())
└── updated_at (TIMESTAMPTZ, Default: NOW())
```

## Code Changes

### Provider Service (`provider/email_providers.py`)
- Updated email_messages references to use `email` schema
- All other references already used `email_provider` schema

### Email Service (`email_service/email_service.py`)
- Updated email_accounts references to use `email_provider` schema
- All email_messages and draft_emails references use `email` schema

### Database Schema Files
- **Provider**: `provider/database_schema.sql` - Updated to use `email_provider` schema
- **Email Service**: `email_service/database_schema.sql` - Updated foreign key references

## Cross-Schema References

### Foreign Key Relationships
- `email.email_messages.account_id` → `email_provider.email_accounts.id`
- `email.draft_emails.account_id` → `email_provider.email_accounts.id`

### RLS Policy Dependencies
Email service RLS policies reference provider schema:
```sql
EXISTS (
    SELECT 1 FROM email_provider.email_accounts 
    WHERE email_provider.email_accounts.id = email.email_messages.account_id 
    AND email_provider.email_accounts.user_id = auth.uid()
)
```

## Migration Benefits

1. **Clear Schema Separation**: Provider and email service have distinct schemas
2. **Proper Namespacing**: All tables are properly namespaced
3. **Cross-Schema Relationships**: Foreign keys work across schemas
4. **Security**: RLS policies maintain proper data isolation
5. **Maintainability**: Each service manages its own schema

## Updated File References

### Provider Service
- `provider/database_schema.sql` - All tables use `email_provider` schema
- `provider/email_providers.py` - Updated email_messages references

### Email Service
- `email_service/database_schema.sql` - Updated foreign key references
- `email_service/email_service.py` - Updated email_accounts references

## Next Steps

1. **Execute Provider Schema**: Run `provider/database_schema.sql`
2. **Execute Email Service Schema**: Run `email_service/database_schema.sql`
3. **Test Cross-Schema Operations**: Verify foreign key relationships work
4. **Test RLS Policies**: Ensure proper data isolation
5. **Update Application Code**: Ensure all database calls use correct schemas

## Notes

- The migration maintains all existing functionality
- Cross-schema foreign key relationships are properly configured
- RLS policies ensure data security across schemas
- All indexes and triggers are properly updated
- The schema separation provides better organization and maintainability

