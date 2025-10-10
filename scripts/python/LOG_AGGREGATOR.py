#!/usr/bin/env python3
import os
import time
import json
from datetime import datetime
import psycopg2

DB_CONFIG = {
    'host': 'aws-0-us-east-2.pooler.supabase.com',
    'port': 6543,
    'database': 'postgres',
    'user': 'postgres.yomagoqdmxszqtdwuhab',
    'password': 'Brain0ps2O2S'
}

def aggregate_logs():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Create logs table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            source VARCHAR(100),
            level VARCHAR(20),
            message TEXT,
            metadata JSONB
        )
    ''')
    conn.commit()
    
    log_files = [
        '/tmp/centerpoint_incremental.log',
        '/tmp/persistent_monitor.log',
        '/tmp/claudeos_health.log',
        '/var/log/docker.log'
    ]
    
    while True:
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        # Read last 100 lines
                        lines = f.readlines()[-100:]
                        for line in lines:
                            if line.strip():
                                cursor.execute('''
                                    INSERT INTO system_logs (source, level, message)
                                    VALUES (%s, %s, %s)
                                    ON CONFLICT DO NOTHING
                                ''', (
                                    os.path.basename(log_file),
                                    'INFO',
                                    line.strip()
                                ))
                    conn.commit()
                except Exception as e:
                    print(f"Error processing {log_file}: {e}")
        
        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    aggregate_logs()
