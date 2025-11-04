#!/usr/bin/env python3
"""
Create copilot_messages table using psycopg2
Direct database connection to create the missing table
"""

import psycopg2
from psycopg2 import sql

# Database connection parameters
DB_PARAMS = {
    "host": "db.yomagoqdmxszqtdwuhab.supabase.co",
    "database": "postgres",
    "user": "postgres",
    "password": "Brain0ps2O2S",
    "port": 5432
}

def create_copilot_messages_table():
    """Create the copilot_messages table and related objects"""
    
    conn = None
    cursor = None
    
    try:
        # Connect to database
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'copilot_messages'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ Table 'copilot_messages' already exists!")
            return True
            
        print("📝 Creating copilot_messages table...")
        
        # Create table
        cursor.execute("""
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
        """)
        
        print("📊 Creating indexes...")
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_copilot_messages_memory_type ON copilot_messages(memory_type);",
            "CREATE INDEX IF NOT EXISTS idx_copilot_messages_is_active ON copilot_messages(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_copilot_messages_created_at ON copilot_messages(created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_copilot_messages_tags ON copilot_messages USING GIN(tags);"
        ]
        
        for index in indexes:
            cursor.execute(index)
            
        print("🔒 Setting up Row Level Security...")
        
        # Enable RLS
        cursor.execute("ALTER TABLE copilot_messages ENABLE ROW LEVEL SECURITY;")
        
        # Create policies
        cursor.execute("""
            CREATE POLICY "Service role full access" ON copilot_messages
                FOR ALL TO service_role
                USING (true)
                WITH CHECK (true);
        """)
        
        cursor.execute("""
            CREATE POLICY "Anon read active messages" ON copilot_messages
                FOR SELECT TO anon
                USING (is_active = true);
        """)
        
        # Grant permissions
        cursor.execute("GRANT ALL ON copilot_messages TO service_role;")
        cursor.execute("GRANT SELECT ON copilot_messages TO anon;")
        
        print("🔧 Creating update trigger...")
        
        # Create trigger function
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        # Create trigger
        cursor.execute("""
            CREATE TRIGGER update_copilot_messages_updated_at 
                BEFORE UPDATE ON copilot_messages 
                FOR EACH ROW 
                EXECUTE FUNCTION update_updated_at_column();
        """)
        
        # Add comment
        cursor.execute("""
            COMMENT ON TABLE copilot_messages IS 
            'Storage for dashboard data, system messages, and persistent memory across all BrainOps systems';
        """)
        
        # Commit changes
        conn.commit()
        print("✅ Table created successfully!")
        
        # Verify table
        cursor.execute("SELECT COUNT(*) FROM copilot_messages;")
        count = cursor.fetchone()[0]
        print(f"📊 Table verification: {count} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("🔌 Database connection closed")

def test_table():
    """Test the table by inserting and reading a record"""
    
    conn = None
    cursor = None
    
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Insert test record
        cursor.execute("""
            INSERT INTO copilot_messages (title, content, role, memory_type)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, ("Dashboard Service Initialized", "Table created successfully", "system", "system_init"))
        
        record_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✅ Test record created with ID: {record_id}")
        
        # Read it back
        cursor.execute("SELECT title, created_at FROM copilot_messages WHERE id = %s", (record_id,))
        title, created_at = cursor.fetchone()
        
        print(f"✅ Test record verified: '{title}' created at {created_at}")
        
        # Clean up test record
        cursor.execute("DELETE FROM copilot_messages WHERE id = %s", (record_id,))
        conn.commit()
        
        print("✅ Test record cleaned up")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Starting copilot_messages table creation...\n")
    
    # Create table
    if create_copilot_messages_table():
        print("\n🧪 Testing table functionality...\n")
        test_table()
        print("\n✅ All done! Dashboard service should now work properly.")
    else:
        print("\n❌ Failed to create table. Please check database connection.")