-- Create marketplace_products table
CREATE TABLE IF NOT EXISTS marketplace_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500),
    url VARCHAR(500),
    price DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'draft',
    qa_score DECIMAL(5,2),
    version VARCHAR(20) DEFAULT '1.0',
    creator_id UUID,
    template_data JSONB,
    last_qa_check TIMESTAMP,
    last_reviewed TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create admin_reviews table
CREATE TABLE IF NOT EXISTS admin_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES marketplace_products(id),
    product_name VARCHAR(255),
    product_type VARCHAR(50),
    qa_score DECIMAL(5,2),
    status VARCHAR(50) DEFAULT 'pending_review',
    priority VARCHAR(20) DEFAULT 'medium',
    submitted_at TIMESTAMP DEFAULT NOW(),
    review_deadline TIMESTAMP,
    review_notes TEXT,
    reviewer VARCHAR(255),
    reviewed_at TIMESTAMP,
    review_comments TEXT,
    required_changes JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_marketplace_products_status ON marketplace_products(status);
CREATE INDEX idx_marketplace_products_type ON marketplace_products(type);
CREATE INDEX idx_admin_reviews_status ON admin_reviews(status);
CREATE INDEX idx_admin_reviews_product_id ON admin_reviews(product_id);

-- Insert sample products for testing
INSERT INTO marketplace_products (name, description, type, price, status, qa_score) VALUES
('Professional Roofing Estimate Template', 'Complete Excel template for creating detailed roofing estimates', 'excel_template', 49.99, 'draft', 75.5),
('Roofing Contract Template', 'Legal contract template for roofing services', 'contract_template', 79.99, 'draft', 82.0),
('Project Management Dashboard', 'Notion template for managing roofing projects', 'notion_template', 59.99, 'draft', 68.5),
('Material Cost Calculator', 'Advanced calculator for roofing material costs', 'calculator', 39.99, 'draft', 71.0),
('Safety Checklist', 'Comprehensive safety checklist for roofing crews', 'checklist', 29.99, 'draft', 88.5);

-- Grant permissions
GRANT ALL ON marketplace_products TO postgres;
GRANT ALL ON admin_reviews TO postgres;