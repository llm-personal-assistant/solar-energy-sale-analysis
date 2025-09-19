-- Email Service Database Schema
-- This schema contains email_messages table and draft functionality

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create email_messages table in email schema
CREATE TABLE IF NOT EXISTS email.email_messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    account_id UUID REFERENCES email_provider.email_accounts(id) ON DELETE CASCADE NOT NULL,
    message_id TEXT NOT NULL, -- Provider's message ID
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

-- Create draft_emails table if it doesn't exist
CREATE TABLE IF NOT EXISTS email.draft_emails (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    account_id UUID NOT NULL,
    to TEXT[] NOT NULL,
    subject TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    is_html BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Foreign key constraints
    CONSTRAINT fk_draft_emails_user_id FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_draft_emails_account_id FOREIGN KEY (account_id) REFERENCES email_provider.email_accounts(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_email_messages_account_id ON email.email_messages(account_id);
CREATE INDEX IF NOT EXISTS idx_email_messages_timestamp ON email.email_messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_email_messages_status ON email.email_messages(status);
CREATE INDEX IF NOT EXISTS idx_draft_emails_user_id ON email.draft_emails(user_id);
CREATE INDEX IF NOT EXISTS idx_draft_emails_account_id ON email.draft_emails(account_id);
CREATE INDEX IF NOT EXISTS idx_draft_emails_updated_at ON email.draft_emails(updated_at DESC);

-- Add RLS (Row Level Security) policies
ALTER TABLE email.email_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE email.draft_emails ENABLE ROW LEVEL SECURITY;

-- Email messages policies
CREATE POLICY "Users can view messages from own accounts" ON email.email_messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM email_provider.email_accounts 
            WHERE email_provider.email_accounts.id = email.email_messages.account_id 
            AND email_provider.email_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert messages to own accounts" ON email.email_messages
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM email_provider.email_accounts 
            WHERE email_provider.email_accounts.id = email.email_messages.account_id 
            AND email_provider.email_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update messages from own accounts" ON email.email_messages
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM email_provider.email_accounts 
            WHERE email_provider.email_accounts.id = email.email_messages.account_id 
            AND email_provider.email_accounts.user_id = auth.uid()
        )
    );

-- Policy: Users can only access their own drafts
CREATE POLICY "Users can access their own drafts" ON email.draft_emails
    FOR ALL USING (auth.uid() = user_id);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION email.update_draft_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER trigger_update_draft_updated_at
    BEFORE UPDATE ON email.draft_emails
    FOR EACH ROW
    EXECUTE FUNCTION email.update_draft_updated_at();