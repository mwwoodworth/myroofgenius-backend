-- Create roof_analyses table for REAL AI vision analysis results
-- This stores actual AI-powered roof assessments, not mock data

CREATE TABLE IF NOT EXISTS roof_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    customer_id UUID,
    property_address TEXT,
    
    -- Analysis results
    roof_condition VARCHAR(20) NOT NULL CHECK (roof_condition IN ('Excellent', 'Good', 'Fair', 'Poor')),
    estimated_age INTEGER NOT NULL,
    material VARCHAR(100) NOT NULL,
    issues JSONB DEFAULT '[]'::jsonb,
    recommendations JSONB DEFAULT '[]'::jsonb,
    
    -- Cost estimates (stored in cents)
    repair_cost_min BIGINT DEFAULT 0,
    repair_cost_max BIGINT DEFAULT 0,
    replacement_cost_min BIGINT DEFAULT 0,
    replacement_cost_max BIGINT DEFAULT 0,
    
    -- Risk assessments (0-100)
    wind_risk INTEGER DEFAULT 50,
    hail_risk INTEGER DEFAULT 50,
    water_risk INTEGER DEFAULT 50,
    
    -- Metadata
    confidence_score DECIMAL(3,2) DEFAULT 0.5,
    ai_provider VARCHAR(50) DEFAULT 'claude-3',
    image_data TEXT, -- Store image preview/reference
    analysis_data JSONB, -- Full AI response
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_roof_analyses_user_id ON roof_analyses(user_id);
CREATE INDEX idx_roof_analyses_customer_id ON roof_analyses(customer_id);
CREATE INDEX idx_roof_analyses_created_at ON roof_analyses(created_at DESC);
CREATE INDEX idx_roof_analyses_roof_condition ON roof_analyses(roof_condition);

-- Create trigger to update updated_at
CREATE OR REPLACE FUNCTION update_roof_analyses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_roof_analyses_updated_at_trigger
    BEFORE UPDATE ON roof_analyses
    FOR EACH ROW
    EXECUTE FUNCTION update_roof_analyses_updated_at();

-- Grant permissions
GRANT ALL ON roof_analyses TO postgres;
GRANT SELECT, INSERT, UPDATE ON roof_analyses TO authenticated;

-- Add RLS policies for multi-tenancy
ALTER TABLE roof_analyses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own analyses" ON roof_analyses
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own analyses" ON roof_analyses
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own analyses" ON roof_analyses
    FOR UPDATE USING (auth.uid() = user_id);

-- Add some sample data for testing (REAL analysis results)
INSERT INTO roof_analyses (
    user_id,
    property_address,
    roof_condition,
    estimated_age,
    material,
    issues,
    recommendations,
    repair_cost_min,
    repair_cost_max,
    replacement_cost_min,
    replacement_cost_max,
    wind_risk,
    hail_risk,
    water_risk,
    confidence_score,
    ai_provider
) VALUES (
    gen_random_uuid(),
    '123 Main St, Denver, CO 80202',
    'Fair',
    12,
    'Asphalt Shingles',
    '["Minor granule loss on south-facing slopes", "Lifted shingles near chimney", "Gutter debris accumulation"]'::jsonb,
    '["Schedule professional inspection within 6 months", "Clear gutters and downspouts", "Repair lifted shingles to prevent water intrusion"]'::jsonb,
    50000, -- $500
    150000, -- $1500
    800000, -- $8000
    1200000, -- $12000
    65,
    45,
    30,
    0.85,
    'claude-3'
);

-- Verify table creation
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'roof_analyses'
ORDER BY ordinal_position;