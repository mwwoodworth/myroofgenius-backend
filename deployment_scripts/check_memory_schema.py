#!/usr/bin/env python3
"""Check memory_entries table schema"""
import psycopg2
import os

# Database connection
DATABASE_URL = "postgresql://postgres:Brain0ps2O2S@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check if memory_entries table exists and get columns
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'memory_entries'
        ORDER BY ordinal_position;
    """)
    
    columns = cur.fetchall()
    
    if columns:
        print("memory_entries table columns:")
        print("-" * 80)
        for col in columns:
            print(f"{col[0]:20} {col[1]:20} {'NULL' if col[2] == 'YES' else 'NOT NULL':10} {col[3] or ''}")
    else:
        print("memory_entries table does not exist")
        
        # Check copilot_messages table instead
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'copilot_messages'
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        if columns:
            print("\ncopilot_messages table columns (used for memory):")
            print("-" * 80)
            for col in columns:
                print(f"{col[0]:20} {col[1]:20} {'NULL' if col[2] == 'YES' else 'NOT NULL':10} {col[3] or ''}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")