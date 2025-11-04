#!/usr/bin/env python3

import psycopg2
from psycopg2 import sql
import sys

# Database connection parameters
DB_PARAMS = {
    'host': 'db.yomagoqdmxszqtdwuhab.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'Brain0ps2O2S',
    'port': '5432'
}

def execute_sql_file(filename):
    """Execute SQL file against the database"""
    
    # Read SQL file
    with open(filename, 'r') as f:
        sql_content = f.read()
    
    # Connect to database
    conn = None
    cursor = None
    
    try:
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected successfully!")
        print("📝 Executing SQL migrations...")
        
        # Execute the entire SQL file
        cursor.execute(sql_content)
        
        print("✅ SQL executed successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (
                'materials_inventory', 
                'suppliers', 
                'supplier_products',
                'material_orders',
                'material_order_items',
                'material_logs'
            )
        """)
        
        tables = cursor.fetchall()
        print(f"\n✅ Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("\n🔌 Database connection closed")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        execute_sql_file(sys.argv[1])
    else:
        # Default to WeatherCraft ERP migrations
        execute_sql_file('/home/mwwoodworth/code/weathercraft-erp/CREATE_MATERIALS_TABLES.sql')