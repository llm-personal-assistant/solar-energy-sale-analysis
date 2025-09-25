-- Database schema for email data sync
-- Tables are created in the 'email' schema

-- Create email schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS email;

-- Set search path to include email schema
SET search_path TO email, public;

-- Email Lead table
-- Stores analyzed email lead information with AI insights
CREATE TABLE IF NOT EXISTS email.email_lead (
    lead_id                     TEXT PRIMARY KEY,
    user_id                     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    owner                       VARCHAR(255),
    subject                     TEXT,
    summary                     TEXT,
    internal_date               BIGINT,
    
    -- Intent analysis fields
    intent_category             TEXT NOT NULL,
    intent_confidence           NUMERIC(4,3) NOT NULL CHECK (intent_confidence >= 0 AND intent_confidence <= 1),
    intent_reason               TEXT NOT NULL,
    
    -- Purchase intent analysis
    purchase_intent_score       SMALLINT NOT NULL CHECK (purchase_intent_score BETWEEN 0 AND 100),
    purchase_intent_reason      TEXT NOT NULL,
    
    -- Sentiment analysis
    sentiment_label             TEXT NOT NULL CHECK (sentiment_label IN ('Positive','Neutral','Negative')),
    sentiment_score             NUMERIC(4,3) NOT NULL CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    sentiment_reason            TEXT NOT NULL,
    
    -- Urgency analysis
    urgency_level               TEXT NOT NULL CHECK (urgency_level IN ('High','Medium','Low')),
    urgency_reason              TEXT NOT NULL,
    
    -- Keywords and pain points
    pain_points                 TEXT[] NOT NULL DEFAULT '{}',
    keywords                    TEXT[] NOT NULL DEFAULT '{}',
    
    -- Sales opportunity analysis
    upsell_value                BOOLEAN NOT NULL,
    upsell_reason               TEXT,
    cross_sell_value            BOOLEAN NOT NULL,
    cross_sell_reason           TEXT,
    
    -- Discount sensitivity
    discount_sensitivity_level  TEXT NOT NULL CHECK (discount_sensitivity_level IN ('High','Medium','Low')),
    discount_sensitivity_reason TEXT,
    
    -- Recommendations and priority
    recommended_steps           TEXT[] NOT NULL DEFAULT '{}',
    priority_level              TEXT NOT NULL CHECK (priority_level IN ('High','Medium','Low')),
    
    -- Metadata
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at                  TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Email Message table
-- Stores individual email messages linked to leads
CREATE TABLE IF NOT EXISTS email.email_message (
    message_id                  TEXT PRIMARY KEY,
    lead_id                     TEXT REFERENCES email.email_lead(lead_id) ON DELETE CASCADE,
    user_id                     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    owner                       VARCHAR(255),
    sender                      VARCHAR(255),
    receiver                    TEXT,
    subject                     TEXT,
    body                        TEXT,
    is_read                     BOOLEAN NOT NULL,
    folder                      TEXT,
    raw_data                    JSONB,
    summary                     TEXT,
    internal_date               BIGINT,
    history_id                  BIGINT,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at                  TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_email_lead_user_id ON email.email_lead(user_id);
CREATE INDEX IF NOT EXISTS idx_email_lead_created_at ON email.email_lead(created_at);
CREATE INDEX IF NOT EXISTS idx_email_lead_priority_level ON email.email_lead(priority_level);
CREATE INDEX IF NOT EXISTS idx_email_lead_intent_category ON email.email_lead(intent_category);

CREATE INDEX IF NOT EXISTS idx_email_message_lead_id ON email.email_message(lead_id);
CREATE INDEX IF NOT EXISTS idx_email_message_user_id ON email.email_message(user_id);
CREATE INDEX IF NOT EXISTS idx_email_message_created_at ON email.email_message(created_at);
CREATE INDEX IF NOT EXISTS idx_email_message_sender ON email.email_message(sender);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION email.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_email_lead_updated_at 
    BEFORE UPDATE ON email.email_lead 
    FOR EACH ROW EXECUTE FUNCTION email.update_updated_at_column();

CREATE TRIGGER update_email_message_updated_at 
    BEFORE UPDATE ON email.email_message 
    FOR EACH ROW EXECUTE FUNCTION email.update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE email.email_lead ENABLE ROW LEVEL SECURITY;
ALTER TABLE email.email_message ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only access their own data
CREATE POLICY "Users can view own email leads" ON email.email_lead
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own email leads" ON email.email_lead
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own email leads" ON email.email_lead
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own email leads" ON email.email_lead
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own email messages" ON email.email_message
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own email messages" ON email.email_message
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own email messages" ON email.email_message
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own email messages" ON email.email_message
    FOR DELETE USING (auth.uid() = user_id);
