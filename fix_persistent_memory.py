#!/usr/bin/env python3
"""
Fix Persistent Memory System
Creates the missing tables that the brain is trying to write to
"""

import asyncio
import asyncpg
import os

async def fix_persistent_memory():
    """Fix the persistent memory database tables"""
    try:
        conn = await asyncpg.connect(
            'postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres'
        )
        
        print("🔧 Fixing persistent memory system...")
        
        # Create the brain_memory table that the brain is trying to write to
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS brain_memory (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                memory_type VARCHAR(50),
                category VARCHAR(100),
                content JSONB NOT NULL,
                associations JSONB,
                embedding vector(1536),
                importance FLOAT DEFAULT 0.5,
                confidence FLOAT DEFAULT 0.8,
                access_count INT DEFAULT 0,
                decay_factor FLOAT DEFAULT 1.0,
                reinforcement_count INT DEFAULT 0,
                source VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW(),
                last_accessed TIMESTAMP DEFAULT NOW(),
                last_modified TIMESTAMP DEFAULT NOW()
            );
        ''')
        
        # Create the thought_stream table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS thought_stream (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                thought JSONB NOT NULL,
                context JSONB,
                triggered_by VARCHAR(255),
                led_to VARCHAR(255),
                quality_score FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        
        # Create indices for better performance
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_brain_memory_type ON brain_memory(memory_type);
            CREATE INDEX IF NOT EXISTS idx_brain_memory_category ON brain_memory(category);
            CREATE INDEX IF NOT EXISTS idx_brain_memory_importance ON brain_memory(importance DESC);
            CREATE INDEX IF NOT EXISTS idx_thought_stream_created ON thought_stream(created_at);
        ''')
        
        print("✅ Brain memory tables created successfully")
        
        # Test the tables by inserting a test thought
        test_result = await conn.fetchval('''
            INSERT INTO brain_memory (memory_type, category, content, importance, source)
            VALUES ('test', 'system', $1, 1.0, 'fix_script')
            RETURNING id
        ''', {"type": "test", "message": "Persistent memory system is now working!"})
        
        print(f"✅ Test thought stored successfully with ID: {test_result}")
        
        # Count existing memories
        memory_count = await conn.fetchval('SELECT COUNT(*) FROM brain_memory')
        thought_count = await conn.fetchval('SELECT COUNT(*) FROM thought_stream')
        
        print(f"📊 Current database status:")
        print(f"   - Brain memories: {memory_count}")
        print(f"   - Thought stream entries: {thought_count}")
        
        await conn.close()
        
        print("🎉 Persistent memory system is now operational!")
        
    except Exception as e:
        print(f"❌ Failed to fix persistent memory: {e}")

if __name__ == "__main__":
    asyncio.run(fix_persistent_memory())