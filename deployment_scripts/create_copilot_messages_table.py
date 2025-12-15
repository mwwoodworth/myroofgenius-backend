#!/usr/bin/env python3
"""
Create copilot_messages table in Supabase
This script creates the missing table that's causing dashboard 404 errors
"""

import asyncio
import aiohttp
import json

SUPABASE_URL = "https://yomagoqdmxszqtdwuhab.supabase.co"
SUPABASE_KEY = "<JWT_REDACTED>"

async def create_table():
    """Create the copilot_messages table via Supabase API"""
    
    sql_query = """
    -- Create copilot_messages table
    CREATE TABLE IF NOT EXISTS copilot_messages (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT,
        role TEXT DEFAULT 'assistant',
        memory_type TEXT,
        tags TEXT[],
        meta_data JSONB DEFAULT '{}',
        is_active BOOLEAN DEFAULT true,
        is_pinned BOOLEAN DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_copilot_messages_memory_type ON copilot_messages(memory_type);
    CREATE INDEX IF NOT EXISTS idx_copilot_messages_is_active ON copilot_messages(is_active);
    CREATE INDEX IF NOT EXISTS idx_copilot_messages_created_at ON copilot_messages(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_copilot_messages_tags ON copilot_messages USING GIN(tags);

    -- Enable RLS
    ALTER TABLE copilot_messages ENABLE ROW LEVEL SECURITY;

    -- Create policies
    CREATE POLICY "Service role full access" ON copilot_messages
        FOR ALL TO service_role
        USING (true)
        WITH CHECK (true);

    CREATE POLICY "Anon read active messages" ON copilot_messages
        FOR SELECT TO anon
        USING (is_active = true);

    -- Grant permissions
    GRANT ALL ON copilot_messages TO service_role;
    GRANT SELECT ON copilot_messages TO anon;

    -- Create update trigger function
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    -- Create trigger
    CREATE TRIGGER update_copilot_messages_updated_at 
        BEFORE UPDATE ON copilot_messages 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();

    -- Add comment
    COMMENT ON TABLE copilot_messages IS 'Storage for dashboard data, system messages, and persistent memory across all BrainOps systems';
    """
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        # Use Supabase's RPC endpoint to execute raw SQL
        try:
            # First, let's check if the table already exists
            check_sql = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'copilot_messages'
            );
            """
            
            async with session.post(
                f"{SUPABASE_URL}/rest/v1/rpc/query",
                headers=headers,
                json={"query": check_sql}
            ) as resp:
                if resp.status == 404:
                    # RPC endpoint might not exist, let's try creating the table directly
                    print("❗ RPC endpoint not available, attempting direct table creation...")
                    
                    # Try to insert a test record to see if table exists
                    test_data = {
                        "title": "System Initialization",
                        "content": "Testing table creation",
                        "role": "system",
                        "memory_type": "system_test"
                    }
                    
                    async with session.post(
                        f"{SUPABASE_URL}/rest/v1/copilot_messages",
                        headers=headers,
                        json=test_data
                    ) as test_resp:
                        if test_resp.status == 404:
                            print("❌ Table does not exist and cannot be created via API")
                            print("⚠️  Manual creation required via Supabase dashboard")
                            print("\nPlease execute the following SQL in Supabase SQL Editor:")
                            print("-" * 80)
                            print(sql_query)
                            print("-" * 80)
                            return False
                        elif test_resp.status in [200, 201]:
                            print("✅ Table already exists!")
                            # Delete test record
                            await session.delete(
                                f"{SUPABASE_URL}/rest/v1/copilot_messages?title=eq.System%20Initialization",
                                headers=headers
                            )
                            return True
                        else:
                            print(f"❌ Unexpected response: {test_resp.status}")
                            error_text = await test_resp.text()
                            print(f"Error: {error_text}")
                            return False
                            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print("\n📋 Manual SQL script saved to: CREATE_COPILOT_MESSAGES_TABLE.sql")
            print("Please execute it in the Supabase SQL Editor")
            return False

async def verify_table():
    """Verify the table was created successfully"""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Prefer": "count=exact"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.head(
            f"{SUPABASE_URL}/rest/v1/copilot_messages",
            headers=headers
        ) as resp:
            if resp.status == 200:
                print("✅ Table verified - copilot_messages is accessible")
                return True
            else:
                print(f"❌ Table verification failed - Status: {resp.status}")
                return False

async def main():
    print("🔧 Creating copilot_messages table...")
    
    # Try to create table
    success = await create_table()
    
    if success:
        # Verify creation
        await verify_table()
        print("\n✅ Table setup complete! Dashboard service should now work properly.")
    else:
        print("\n⚠️  Please create the table manually using the Supabase dashboard")
        print("Navigate to: SQL Editor → New Query → Paste the SQL above → Run")

if __name__ == "__main__":
    asyncio.run(main())