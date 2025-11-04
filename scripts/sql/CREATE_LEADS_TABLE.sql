-- Create leads table for MyRoofGenius
CREATE TABLE IF NOT EXISTS leads (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  phone VARCHAR(50),
  company VARCHAR(255),
  source VARCHAR(100) DEFAULT 'website',
  offer VARCHAR(255),
  interests JSONB DEFAULT '[]'::jsonb,
  metadata JSONB DEFAULT '{}'::jsonb,
  status VARCHAR(50) DEFAULT 'new',
  score INTEGER DEFAULT 0,
  converted_at TIMESTAMPTZ,
  customer_id UUID REFERENCES customers(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(email)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);

-- Create email sequences table
CREATE TABLE IF NOT EXISTS email_sequences (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  email VARCHAR(255) NOT NULL,
  sequence JSONB NOT NULL,
  status VARCHAR(50) DEFAULT 'active',
  current_step INTEGER DEFAULT 0,
  last_sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create email logs table
CREATE TABLE IF NOT EXISTS email_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id UUID REFERENCES leads(id),
  email VARCHAR(255) NOT NULL,
  subject VARCHAR(500),
  template VARCHAR(100),
  status VARCHAR(50),
  sent_at TIMESTAMPTZ DEFAULT NOW(),
  opened_at TIMESTAMPTZ,
  clicked_at TIMESTAMPTZ,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_sequences_updated_at BEFORE UPDATE ON email_sequences
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL ON leads TO authenticated;
GRANT ALL ON email_sequences TO authenticated;
GRANT ALL ON email_logs TO authenticated;

-- Enable RLS
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_sequences ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Public can insert leads" ON leads
  FOR INSERT TO anon, authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can view all leads" ON leads
  FOR SELECT TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can update leads" ON leads
  FOR UPDATE TO authenticated
  USING (true);

-- Insert test data
INSERT INTO leads (email, name, source, offer, interests, metadata, score) VALUES
  ('demo@example.com', 'Demo User', 'website', 'ai-analysis', '["roofing", "ai"]'::jsonb, '{"test": true}'::jsonb, 85),
  ('test@roofing.com', 'Test Contractor', 'pricing', 'calculator', '["automation", "crm"]'::jsonb, '{"referrer": "google"}'::jsonb, 72)
ON CONFLICT (email) DO NOTHING;

-- Success message
SELECT 'Leads tables created successfully!' as status,
       COUNT(*) as lead_count
FROM leads;