# Database Schema Migration Summary

## Overview
Successfully migrated `email_messages` table and related components from `provider/database_schema.sql` to `email_service/database_schema.sql` with schema change from `email_provider` to `email`.

## What Was Migrated

### From Provider to Email Service
- **email_messages table**: Complete table definition with all columns and constraints
- **Indexes**: All email_messages related indexes
- **RLS Policies**: All email_messages related Row Level Security policies
- **Schema Reference**: Changed from `email_provider` to `email` schema

### Database Schema Changes

#### Before (Provider Schema)
```sql
-- In provider/database_schema.sql
CREATE TABLE IF NOT EXISTS email_messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    account_id UUID REFERENCES email_accounts(id) ON DELETE CASCADE NOT NULL,
    message_id TEXT NOT NULL,
    subject TEXT,
    sender TEXT,
    recipient TEXT,
    body TEXT,
    timestamp TIMESTAMP WITH TIME ZONE,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(account_id, message_id)
);
```

#### After (Email Service Schema)
```sql
-- In email_service/database_schema.sql
CREATE TABLE IF NOT EXISTS email.email_messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    account_id UUID REFERENCES email.email_accounts(id) ON DELETE CASCADE NOT NULL,
    message_id TEXT NOT NULL,
    subject TEXT,
    sender TEXT,
    recipient TEXT,
    body TEXT,
    timestamp TIMESTAMP WITH TIME ZONE,
    is_read BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'received' CHECK (status IN ('draft', 'sent', 'received')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(account_id, message_id)
);
```

## Code Changes

### Email Service Python Code
Updated all database references in `email_service.py`:
- `self.admin.schema('email_provider')` → `self.admin.schema('email')`
- All table references now use `email` schema

### Affected Methods
- `get_user_email_accounts()`
- `_refresh_and_save_tokens()`
- `get_emails()`
- `send_email()`
- `save_draft()`
- `get_drafts()`
- `get_draft()`
- `update_draft()`
- `delete_draft()`
- `send_draft()`

## Database Schema Structure

### Email Service Schema (`email`)
```
email.email_messages
├── id (UUID, Primary Key)
├── account_id (UUID, Foreign Key to email.email_accounts)
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
├── account_id (UUID, Foreign Key to email.email_accounts)
├── to (TEXT[])
├── subject (TEXT)
├── body (TEXT)
├── is_html (BOOLEAN, Default: FALSE)
├── created_at (TIMESTAMPTZ, Default: NOW())
└── updated_at (TIMESTAMPTZ, Default: NOW())
```

### Provider Schema (unchanged)
```
email_accounts
├── id (UUID, Primary Key)
├── user_id (UUID, Foreign Key to auth.users)
├── email (TEXT)
├── provider (TEXT, Check: 'google'|'outlook'|'yahoo')
├── access_token (TEXT)
├── refresh_token (TEXT)
├── is_active (BOOLEAN, Default: TRUE)
├── created_at (TIMESTAMP WITH TIME ZONE, Default: NOW())
└── updated_at (TIMESTAMP WITH TIME ZONE, Default: NOW())

oauth_states
├── id (UUID, Primary Key)
├── state (TEXT, Unique)
├── user_id (UUID, Foreign Key to auth.users)
├── provider (TEXT, Check: 'google'|'outlook'|'yahoo')
├── created_at (TIMESTAMP WITH TIME ZONE, Default: NOW())
├── expires_at (TIMESTAMP WITH TIME ZONE)
├── verified (BOOLEAN, Default: FALSE)
└── verified_at (TIMESTAMP WITH TIME ZONE)
```

## Migration Benefits

1. **Clear Separation**: Email operations are now in their own schema
2. **Better Organization**: Email-related tables are grouped together
3. **Enhanced Status Tracking**: Added status column to email_messages
4. **Improved Security**: RLS policies are properly scoped to email schema
5. **Maintainability**: Each service manages its own database schema

## Migration Steps

1. **Run Email Service Schema**: Execute `email_service/database_schema.sql`
2. **Update Code References**: All Python code now uses `email` schema
3. **Verify Data Migration**: Ensure existing data is accessible
4. **Test Functionality**: Verify all email operations work correctly

## Notes

- The `email.email_accounts` table is still referenced by email service but managed by provider service
- Foreign key relationships are maintained between schemas
- RLS policies ensure proper data isolation between users
- The migration maintains backward compatibility for existing data

## Next Steps

1. Execute the email service database schema
2. Test email operations to ensure proper functionality
3. Monitor for any schema-related issues
4. Update any external references to use the new schema structure
