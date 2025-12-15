#!/usr/bin/env python3
"""
Setup marketplace tables using Supabase API
"""

import requests
import json
import os

SUPABASE_URL = "https://yomagoqdmxszqtdwuhab.supabase.co"
SUPABASE_KEY = "<JWT_REDACTED>"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Create tables via RPC if needed
create_tables_sql = """
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
"""

# Try to insert sample products
sample_products = [
    {
        "name": "Professional Roofing Estimate Template",
        "description": "Complete Excel template for creating detailed roofing estimates",
        "type": "excel_template",
        "price": 49.99,
        "status": "draft",
        "qa_score": 75.5,
        "file_path": "/home/mwwoodworth/code/products/roofing_estimate_template.xlsx"
    },
    {
        "name": "Roofing Contract Template",
        "description": "Legal contract template for roofing services",
        "type": "contract_template",
        "price": 79.99,
        "status": "draft",
        "qa_score": 82.0,
        "file_path": "/home/mwwoodworth/code/products/roofing_contract.pdf"
    },
    {
        "name": "Project Management Dashboard",
        "description": "Notion template for managing roofing projects",
        "type": "notion_template",
        "price": 59.99,
        "status": "draft",
        "qa_score": 68.5,
        "template_data": {"type": "notion", "features": ["kanban", "calendar", "tasks"]}
    },
    {
        "name": "Material Cost Calculator",
        "description": "Advanced calculator for roofing material costs",
        "type": "calculator",
        "price": 39.99,
        "status": "draft",
        "qa_score": 71.0,
        "url": "https://myroofgenius.com/tools/material-calculator"
    },
    {
        "name": "Safety Checklist",
        "description": "Comprehensive safety checklist for roofing crews",
        "type": "checklist",
        "price": 29.99,
        "status": "draft",
        "qa_score": 88.5,
        "file_path": "/home/mwwoodworth/code/products/safety_checklist.pdf"
    }
]

print("Setting up marketplace tables...")

# First, check if tables exist by trying to query them
try:
    # Check marketplace_products
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/marketplace_products?limit=1",
        headers=headers
    )
    
    if response.status_code == 404:
        print("❌ Tables don't exist yet. Please create them via Supabase dashboard.")
        print("\nSQL to execute:")
        print(create_tables_sql)
    elif response.status_code == 200:
        print("✅ marketplace_products table exists")
        
        # Check if empty and insert sample data
        products = response.json()
        if len(products) == 0:
            print("Inserting sample products...")
            
            for product in sample_products:
                resp = requests.post(
                    f"{SUPABASE_URL}/rest/v1/marketplace_products",
                    headers=headers,
                    json=product
                )
                if resp.status_code in [200, 201]:
                    print(f"✅ Added: {product['name']}")
                else:
                    print(f"❌ Failed to add {product['name']}: {resp.status_code}")
        else:
            print(f"Table already has {len(products)} products")
    
    # Check admin_reviews
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/admin_reviews?limit=1",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✅ admin_reviews table exists")
    else:
        print("❌ admin_reviews table missing")
        
except Exception as e:
    print(f"Error: {str(e)}")

print("\nTable setup complete!")