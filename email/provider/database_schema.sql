-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create email_accounts table
CREATE TABLE IF NOT EXISTS email_provider.email_accounts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    email TEXT NOT NULL,
    provider TEXT NOT NULL CHECK (provider IN ('google', 'outlook', 'yahoo')),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, email, provider)
);

-- Email messages table moved to email_service/database_schema.sql

-- Create oauth_states table for OAuth flow
CREATE TABLE IF NOT EXISTS email_provider.oauth_states (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    state TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider IN ('google', 'outlook', 'yahoo')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE
);

-- For existing deployments, run the following to add new columns:
-- ALTER TABLE email_provider.oauth_states ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT FALSE;
-- ALTER TABLE email_provider.oauth_states ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITH TIME ZONE;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_email_accounts_user_id ON email_provider.email_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_email_accounts_provider ON email_provider.email_accounts(provider);
-- Email messages indexes moved to email_service/database_schema.sql
CREATE INDEX IF NOT EXISTS idx_oauth_states_state ON email_provider.oauth_states(state);
CREATE INDEX IF NOT EXISTS idx_oauth_states_expires_at ON email_provider.oauth_states(expires_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';


CREATE TRIGGER update_email_accounts_updated_at BEFORE UPDATE ON email_provider.email_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create RLS (Row Level Security) policies
ALTER TABLE email_provider.email_accounts ENABLE ROW LEVEL SECURITY;
-- Email messages RLS policies moved to email_service/database_schema.sql
ALTER TABLE email_provider.oauth_states ENABLE ROW LEVEL SECURITY;

-- Email accounts policies
CREATE POLICY "Users can view own email accounts" ON email_provider.email_accounts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own email accounts" ON email_provider.email_accounts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own email accounts" ON email_provider.email_accounts
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own email accounts" ON email_provider.email_accounts
    FOR DELETE USING (auth.uid() = user_id);

-- Email messages policies moved to email_service/database_schema.sql

-- OAuth states policies
CREATE POLICY "Users can view own oauth states" ON email_provider.oauth_states
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own oauth states" ON email_provider.oauth_states
    FOR INSERT WITH CHECK (auth.uid() = user_id);


-- Create function to clean up expired OAuth states
CREATE OR REPLACE FUNCTION cleanup_expired_oauth_states()
RETURNS void AS $$
BEGIN
    DELETE FROM email_provider.oauth_states WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to clean up expired states (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-oauth-states', '0 * * * *', 'SELECT cleanup_expired_oauth_states();');
