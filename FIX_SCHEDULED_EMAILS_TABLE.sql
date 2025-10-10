-- Fix scheduled_emails table creation without auth.users dependency
-- Since auth schema doesn't exist in this database, we'll use a different approach

-- Drop if exists
DROP TABLE IF EXISTS scheduled_emails CASCADE;

-- Create scheduled_emails table without auth.users reference
CREATE TABLE scheduled_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID, -- No foreign key constraint since auth.users doesn't exist
    email VARCHAR(255) NOT NULL,
    sequence_type VARCHAR(50) NOT NULL CHECK (sequence_type IN (
        'welcome',
        'abandoned_cart',
        'win_back',
        'trial_ending',
        'nurture_leads',
        'upsell_sequence'
    )),
    template VARCHAR(50) NOT NULL,
    subject TEXT NOT NULL,
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    personalization_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_scheduled_emails_user_id ON scheduled_emails(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_emails_status ON scheduled_emails(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_emails_scheduled_for ON scheduled_emails(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_scheduled_emails_sequence_type ON scheduled_emails(sequence_type);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_scheduled_emails_updated_at
    BEFORE UPDATE ON scheduled_emails
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Verify table was created
SELECT 'scheduled_emails' as table_name, COUNT(*) as row_count FROM scheduled_emails;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ scheduled_emails table created successfully!';
END $$;