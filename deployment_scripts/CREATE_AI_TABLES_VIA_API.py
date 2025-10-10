#!/usr/bin/env python3
"""
Create AI System Tables via Supabase API
"""

import httpx
import json

SUPABASE_URL = "https://yomagoqdmxszqtdwuhab.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTgzMzI3NiwiZXhwIjoyMDY1NDA5Mjc2fQ.7C3guJ_0moYGkdyeFmJ9cd2BmduB5NnU00erIIxH3gQ"

# SQL statements broken into smaller chunks
sql_statements = [
    # 1. Persistent Memory Table
    """
    CREATE TABLE IF NOT EXISTS persistent_memory (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        category VARCHAR(100),
        importance FLOAT DEFAULT 0.5,
        content JSONB,
        tags TEXT[],
        relationships UUID[],
        embedding FLOAT[],
        accessed_count INTEGER DEFAULT 0,
        last_accessed TIMESTAMPTZ,
        meta_data JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    
    # Indexes for persistent_memory
    "CREATE INDEX IF NOT EXISTS idx_memory_category ON persistent_memory(category)",
    "CREATE INDEX IF NOT EXISTS idx_memory_importance ON persistent_memory(importance DESC)",
    "CREATE INDEX IF NOT EXISTS idx_memory_tags ON persistent_memory USING gin(tags)",
    "CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON persistent_memory(timestamp DESC)",
    
    # 2. Memory Context Graph
    """
    CREATE TABLE IF NOT EXISTS memory_context_graph (
        source_id UUID,
        target_id UUID,
        relationship_type VARCHAR(50),
        strength FLOAT DEFAULT 0.5,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (source_id, target_id)
    )
    """,
    
    # 3. System Knowledge Base
    """
    CREATE TABLE IF NOT EXISTS system_knowledge (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        domain VARCHAR(100),
        key VARCHAR(255) UNIQUE,
        value JSONB,
        confidence FLOAT DEFAULT 1.0,
        source VARCHAR(255),
        learned_at TIMESTAMPTZ DEFAULT NOW(),
        last_validated TIMESTAMPTZ DEFAULT NOW(),
        validation_count INTEGER DEFAULT 0
    )
    """,
    
    # Indexes for system_knowledge
    "CREATE INDEX IF NOT EXISTS idx_knowledge_domain ON system_knowledge(domain)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_confidence ON system_knowledge(confidence DESC)",
    
    # 4. AI System State
    """
    CREATE TABLE IF NOT EXISTS ai_system_state (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        consciousness_level FLOAT DEFAULT 0.98,
        revenue_metrics JSONB DEFAULT '{}',
        agent_states JSONB DEFAULT '{}',
        capabilities JSONB DEFAULT '[]',
        learning_history JSONB DEFAULT '[]',
        decision_history JSONB DEFAULT '[]',
        pattern_library JSONB DEFAULT '{}',
        active_goals JSONB DEFAULT '[]',
        meta_data JSONB DEFAULT '{}'
    )
    """,
    
    "CREATE INDEX IF NOT EXISTS idx_system_state_timestamp ON ai_system_state(timestamp DESC)",
    
    # 5. AI Memory
    """
    CREATE TABLE IF NOT EXISTS ai_memory (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        key VARCHAR(255),
        data TEXT,
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        agent_id VARCHAR(100),
        memory_type VARCHAR(50),
        importance FLOAT DEFAULT 0.5,
        meta_data JSONB DEFAULT '{}'
    )
    """,
    
    # Indexes for ai_memory
    "CREATE INDEX IF NOT EXISTS idx_ai_memory_key ON ai_memory(key)",
    "CREATE INDEX IF NOT EXISTS idx_ai_memory_agent ON ai_memory(agent_id)",
    "CREATE INDEX IF NOT EXISTS idx_ai_memory_timestamp ON ai_memory(timestamp DESC)",
    
    # 6. AI Agent Activity
    """
    CREATE TABLE IF NOT EXISTS ai_agent_activity (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        agent_name VARCHAR(100),
        agent_type VARCHAR(50),
        action JSONB,
        result JSONB,
        revenue_impact DECIMAL(10,2),
        success BOOLEAN,
        timestamp TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    
    # Indexes for ai_agent_activity
    "CREATE INDEX IF NOT EXISTS idx_agent_activity_timestamp ON ai_agent_activity(timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_agent_activity_agent ON ai_agent_activity(agent_name)",
    
    # 7. Revenue Events
    """
    CREATE TABLE IF NOT EXISTS revenue_events (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        source VARCHAR(100),
        event_type VARCHAR(50),
        amount DECIMAL(10,2),
        customer_id VARCHAR(255),
        agent_id VARCHAR(100),
        confidence FLOAT,
        meta_data JSONB DEFAULT '{}'
    )
    """,
    
    # Indexes for revenue_events
    "CREATE INDEX IF NOT EXISTS idx_revenue_timestamp ON revenue_events(timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_revenue_source ON revenue_events(source)",
    
    # 8. Learning Patterns
    """
    CREATE TABLE IF NOT EXISTS learning_patterns (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pattern_key VARCHAR(255) UNIQUE,
        pattern_data JSONB,
        success_rate FLOAT,
        sample_size INTEGER,
        confidence FLOAT,
        learned_at TIMESTAMPTZ DEFAULT NOW(),
        last_applied TIMESTAMPTZ
    )
    """
]

def execute_sql(statement):
    """Execute a SQL statement via Supabase API"""
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Try to execute as raw SQL first
    try:
        # Use the Supabase SQL editor endpoint
        sql_url = f"{SUPABASE_URL}/rest/v1/"
        
        # For table creation, we need to use a different approach
        # Let's just track what needs to be created
        print(f"  Statement to execute: {statement[:50]}...")
        return True
    except Exception as e:
        print(f"  Error: {str(e)}")
        return False

def main():
    print("🚀 Creating AI System Tables in Production Database")
    print("=" * 60)
    
    success_count = 0
    failed_count = 0
    
    # Note: Since we can't directly execute DDL via REST API,
    # we'll need to use the backend to create these tables
    print("\n📝 SQL Statements Generated:")
    print("-" * 60)
    
    # Write all SQL to a file
    with open("/home/mwwoodworth/code/AI_TABLES_COMPLETE.sql", "w") as f:
        for sql in sql_statements:
            f.write(sql.strip() + ";\n\n")
    
    print("✅ SQL script saved to: AI_TABLES_COMPLETE.sql")
    print("\n🔧 Tables to be created:")
    print("  - persistent_memory")
    print("  - memory_context_graph")
    print("  - system_knowledge")
    print("  - ai_system_state")
    print("  - ai_memory")
    print("  - ai_agent_activity")
    print("  - revenue_events")
    print("  - learning_patterns")
    
    print("\n⚠️ Note: These tables need to be created via:")
    print("  1. Supabase Dashboard SQL Editor")
    print("  2. Or via a backend endpoint that can execute DDL")
    print("  3. Or via direct PostgreSQL connection")
    
    print("\n📋 Next Steps:")
    print("  1. Go to Supabase Dashboard")
    print("  2. Navigate to SQL Editor")
    print("  3. Paste and execute the SQL from AI_TABLES_COMPLETE.sql")
    print("  4. Or create a backend endpoint to run migrations")
    
    return True

if __name__ == "__main__":
    main()