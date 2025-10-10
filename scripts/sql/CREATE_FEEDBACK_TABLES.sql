-- Create NPS and Feedback System Tables
-- For BrainOps v6.0

-- NPS Responses Table
CREATE TABLE IF NOT EXISTS nps_responses (
    id SERIAL PRIMARY KEY,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 10),
    category VARCHAR(20) NOT NULL, -- promoter, passive, detractor
    feedback TEXT,
    would_recommend BOOLEAN DEFAULT true,
    user_id INTEGER,
    org_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Testimonials Table
CREATE TABLE IF NOT EXISTS testimonials (
    id SERIAL PRIMARY KEY,
    testimonial TEXT NOT NULL,
    use_case VARCHAR(255) NOT NULL,
    results TEXT,
    company_name VARCHAR(255),
    role VARCHAR(255),
    permission_to_use BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
    user_id INTEGER,
    org_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Referral Codes Table
CREATE TABLE IF NOT EXISTS referral_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER,
    org_id INTEGER,
    uses_count INTEGER DEFAULT 0,
    successful_count INTEGER DEFAULT 0,
    total_earned DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Referral Applications Table
CREATE TABLE IF NOT EXISTS referral_applications (
    id SERIAL PRIMARY KEY,
    referral_code VARCHAR(50) NOT NULL,
    org_id VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, expired
    discount_percentage INTEGER DEFAULT 20,
    discount_months INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_nps_responses_created_at ON nps_responses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_nps_responses_category ON nps_responses(category);
CREATE INDEX IF NOT EXISTS idx_testimonials_status ON testimonials(status);
CREATE INDEX IF NOT EXISTS idx_testimonials_permission ON testimonials(permission_to_use);
CREATE INDEX IF NOT EXISTS idx_referral_codes_code ON referral_codes(code);
CREATE INDEX IF NOT EXISTS idx_referral_applications_code ON referral_applications(referral_code);

-- Insert sample testimonials for display
INSERT INTO testimonials (
    testimonial, use_case, results, company_name, role, 
    permission_to_use, status, created_at
) VALUES 
(
    'BrainOps transformed our roofing business. We went from manual estimates to AI-powered proposals in minutes.',
    'Commercial roofing estimation',
    'Reduced estimation time by 85%, increased close rate by 40%',
    'Apex Roofing Solutions',
    'CEO',
    true,
    'approved',
    NOW() - INTERVAL '7 days'
),
(
    'The AI estimation is incredibly accurate. It catches details we used to miss and helps us price competitively.',
    'Residential roofing projects',
    'Improved accuracy by 95%, won 30% more bids',
    'Summit Roof Experts',
    'Operations Manager',
    true,
    'approved',
    NOW() - INTERVAL '14 days'
),
(
    'Customer management and automated follow-ups have been game changers. We never lose track of leads anymore.',
    'CRM and lead management',
    'Converted 50% more leads, saved 10 hours per week',
    'Premier Roofing Co',
    'Sales Director',
    true,
    'approved',
    NOW() - INTERVAL '21 days'
);

-- Insert sample NPS responses
INSERT INTO nps_responses (score, category, feedback, would_recommend, created_at)
VALUES 
(9, 'promoter', 'Excellent system, saves us hours every day', true, NOW() - INTERVAL '1 day'),
(10, 'promoter', 'Best investment we made this year', true, NOW() - INTERVAL '3 days'),
(8, 'passive', 'Good system, still learning all features', true, NOW() - INTERVAL '5 days'),
(9, 'promoter', 'AI estimation is incredibly accurate', true, NOW() - INTERVAL '7 days'),
(10, 'promoter', 'Transformed our business operations completely', true, NOW() - INTERVAL '10 days');

-- Grant permissions
GRANT ALL ON nps_responses TO postgres;
GRANT ALL ON testimonials TO postgres;
GRANT ALL ON referral_codes TO postgres;
GRANT ALL ON referral_applications TO postgres;
GRANT ALL ON nps_responses_id_seq TO postgres;
GRANT ALL ON testimonials_id_seq TO postgres;
GRANT ALL ON referral_codes_id_seq TO postgres;
GRANT ALL ON referral_applications_id_seq TO postgres;