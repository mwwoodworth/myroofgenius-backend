#!/home/matt-woodworth/ai-systems/venv/bin/python
"""
Complete Database Migration Script
Creates all tables and structures for the full AI-OS
"""

import asyncio
import asyncpg
import os
from datetime import datetime

async def run_migrations():
    # Connect to production database
    conn = await asyncpg.connect(
        'postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:5432/postgres'
    )
    
    print("Running complete database migrations...")
    
    # Create webhook tables
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS webhook_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                service VARCHAR(50),
                event_type VARCHAR(100),
                payload JSONB,
                status VARCHAR(50) DEFAULT 'pending',
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                error TEXT
            );
        """)
    except Exception as e:
        print(f"Webhook table exists or error: {e}")
    
    try:
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_webhook_events_service ON webhook_events(service);
            CREATE INDEX IF NOT EXISTS idx_webhook_events_status ON webhook_events(status);
            CREATE INDEX IF NOT EXISTS idx_webhook_events_received ON webhook_events(received_at);
        """)
    except:
        pass
    
    # Create logs table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id BIGSERIAL PRIMARY KEY,
            source VARCHAR(50),
            timestamp TIMESTAMP,
            level VARCHAR(20),
            message TEXT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_logs_source ON logs(source);
        CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
    """)
    
    # Create automation tables
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS automation_rules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            trigger_type VARCHAR(50),
            trigger_config JSONB,
            conditions JSONB,
            actions JSONB,
            enabled BOOLEAN DEFAULT true,
            cooldown INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS automation_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            rule_id UUID REFERENCES automation_rules(id),
            trigger_data JSONB,
            status VARCHAR(50),
            result JSONB,
            error TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_automation_rules_enabled ON automation_rules(enabled);
        CREATE INDEX IF NOT EXISTS idx_automation_executions_rule_id ON automation_executions(rule_id);
    """)
    
    # Create deployments table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS deployments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            deployment_id VARCHAR(255) UNIQUE,
            service VARCHAR(50),
            url TEXT,
            status VARCHAR(50),
            error JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            failed_at TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status);
        CREATE INDEX IF NOT EXISTS idx_deployments_service ON deployments(service);
    """)
    
    # Create alerts table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            type VARCHAR(100),
            severity VARCHAR(20),
            context JSONB,
            acknowledged BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            acknowledged_at TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(type);
        CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
        CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged);
    """)
    
    # Create metrics table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id BIGSERIAL PRIMARY KEY,
            metric_name VARCHAR(100),
            metric_value FLOAT,
            tags JSONB,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);
        CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);
    """)
    
    # Create customers table if not exists
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE,
            name VARCHAR(255),
            company VARCHAR(255),
            phone VARCHAR(50),
            address JSONB,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
    """)
    
    # Create jobs table if not exists
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            customer_id UUID REFERENCES customers(id),
            title VARCHAR(255),
            description TEXT,
            status VARCHAR(50),
            priority VARCHAR(20),
            assigned_to VARCHAR(255),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_jobs_customer_id ON jobs(customer_id);
        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
    """)
    
    # Create orders table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            customer_id UUID REFERENCES customers(id),
            stripe_payment_intent VARCHAR(255),
            status VARCHAR(50),
            total DECIMAL(10, 2),
            items JSONB,
            paid_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
    """)
    
    # Insert default automation rules
    await conn.execute("""
        INSERT INTO automation_rules (name, description, trigger_type, conditions, actions, enabled)
        VALUES 
        ('Auto-deploy on main push', 'Deploy when code is pushed to main branch', 'webhook', 
         '{"ref": "refs/heads/main"}', 
         '[{"type": "deployment", "service": "vercel", "operation": "deploy"}]', true),
        
        ('High error rate alert', 'Alert when error rate exceeds threshold', 'condition',
         '{"type": "metric", "metric": "error_rate", "operator": "gt", "threshold": 0.05}',
         '[{"type": "notification", "channels": ["slack"], "message": "High error rate detected"}]', true),
        
        ('Auto-scale on high CPU', 'Scale up when CPU usage is high', 'condition',
         '{"type": "metric", "metric": "cpu_usage", "operator": "gt", "threshold": 80}',
         '[{"type": "scaling", "service": "render", "scale_type": "horizontal", "value": 2}]', true)
         
        ON CONFLICT DO NOTHING;
    """)
    
    print("✅ All database migrations completed successfully")
    
    # Verify tables
    tables = await conn.fetch("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' 
        ORDER BY tablename;
    """)
    
    print(f"\n📊 Database tables ({len(tables)} total):")
    for table in tables:
        print(f"  - {table['tablename']}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migrations())