-- Complete Database Fix for BrainOps v3.1.14
-- Run this in Supabase SQL Editor to fix all remaining issues

-- ============================================
-- 1. Fix memory_sync table (missing memory_id column)
-- ============================================
-- Check current columns
SELECT 'Current memory_sync columns:' as info;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'memory_sync'
ORDER BY ordinal_position;

-- Add missing column
ALTER TABLE memory_sync 
ADD COLUMN IF NOT EXISTS memory_id VARCHAR(255) NOT NULL DEFAULT 'pending';

-- Remove default after adding
ALTER TABLE memory_sync 
ALTER COLUMN memory_id DROP DEFAULT;

-- ============================================
-- 2. Ensure all required tables exist
-- ============================================

-- Memory entries table (already exists based on logs)
CREATE TABLE IF NOT EXISTS memory_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL,
    memory_type VARCHAR(100) NOT NULL,
    content TEXT,
    meta_data JSON,
    embedding JSON,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    source VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    expires_at TIMESTAMP WITHOUT TIME ZONE,
    version INTEGER DEFAULT 1,
    tags JSON,
    importance_score INTEGER,
    owner_type VARCHAR(100) NOT NULL,
    owner_id VARCHAR(255) NOT NULL,
    key VARCHAR(255) NOT NULL,
    context_json JSONB NOT NULL DEFAULT '{}',
    category VARCHAR(100),
    accessed_at TIMESTAMP WITHOUT TIME ZONE,
    description TEXT,
    is_active VARCHAR(10) DEFAULT 'true',
    value TEXT NOT NULL
);

-- Cross-AI memory table
CREATE TABLE IF NOT EXISTS cross_ai_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding FLOAT[],
    source_agent VARCHAR(100),
    target_agents TEXT[],
    sync_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    importance_score FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    tags TEXT[],
    category VARCHAR(100),
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    is_active BOOLEAN DEFAULT true
);

-- DB sync status table
CREATE TABLE IF NOT EXISTS db_sync_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 3. Create indexes for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_memory_entries_owner ON memory_entries(owner_type, owner_id);
CREATE INDEX IF NOT EXISTS idx_memory_entries_key ON memory_entries(key);
CREATE INDEX IF NOT EXISTS idx_memory_entries_created ON memory_entries(created_at);

CREATE INDEX IF NOT EXISTS idx_cross_ai_memory_type ON cross_ai_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_cross_ai_memory_agent ON cross_ai_memory(source_agent);
CREATE INDEX IF NOT EXISTS idx_cross_ai_memory_created ON cross_ai_memory(created_at);

CREATE INDEX IF NOT EXISTS idx_memory_sync_memory_id ON memory_sync(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_sync_status ON memory_sync(sync_status);

-- ============================================
-- 4. Test the fixes
-- ============================================
-- Test memory_sync insert
INSERT INTO memory_sync (memory_id, source_agent, target_agent, sync_status)
VALUES ('test_' || gen_random_uuid()::text, 'test_source', 'test_target', 'pending')
ON CONFLICT DO NOTHING;

-- Verify all tables
SELECT 'Tables created/verified:' as info;
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('memory_entries', 'memory_sync', 'cross_ai_memory', 'db_sync_status')
ORDER BY table_name;

-- Clean up test data
DELETE FROM memory_sync WHERE memory_id LIKE 'test_%';

-- ============================================
-- 5. Summary
-- ============================================
SELECT 'Database fixes completed!' as status;
SELECT 
    'memory_sync' as table_name,
    EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'memory_sync' AND column_name = 'memory_id') as has_memory_id_column;