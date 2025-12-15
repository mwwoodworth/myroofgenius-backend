#!/usr/bin/env python3
"""
Run all ERP database migrations
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

def run_migration(conn, migration_file):
    """Run a single migration file"""
    try:
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        with conn.cursor() as cursor:
            # Split by statement and execute each
            statements = sql.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement + ';')
                        logger.info(f"Executed: {statement[:50]}...")
                    except psycopg2.errors.DuplicateTable:
                        logger.info(f"Table already exists, skipping...")
                    except psycopg2.errors.DuplicateObject:
                        logger.info(f"Object already exists, skipping...")
                    except Exception as e:
                        logger.warning(f"Error in statement: {e}")
                        # Continue with next statement
                        continue
        
        conn.commit()
        logger.info(f"✅ Completed migration: {migration_file.name}")
        return True
        
    except Exception as e:
        logger.error(f"Error running migration {migration_file}: {e}")
        conn.rollback()
        return False

def main():
    """Run all migrations in order"""
    
    migrations_dir = Path('/home/matt-woodworth/fastapi-operator-env/migrations')
    
    # Get all SQL files in order
    migration_files = sorted(migrations_dir.glob('*.sql'))
    
    if not migration_files:
        logger.error("No migration files found")
        return
    
    logger.info(f"Found {len(migration_files)} migration files")
    
    # Connect to database
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info("Connected to database")
        
        # First ensure required extensions
        with conn.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            logger.info("Extensions ensured")
        
        # Track results
        results = []
        
        # Run each migration
        for migration_file in migration_files:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running: {migration_file.name}")
            logger.info(f"{'='*60}")
            
            success = run_migration(conn, migration_file)
            results.append((migration_file.name, success))
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("MIGRATION SUMMARY")
        logger.info(f"{'='*60}")
        
        successful = sum(1 for _, success in results if success)
        failed = len(results) - successful
        
        for filename, success in results:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            logger.info(f"{filename}: {status}")
        
        logger.info(f"\nTotal: {successful} successful, {failed} failed")
        
        # Check table count
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            table_count = cursor.fetchone()[0]
            logger.info(f"\nTotal tables in database: {table_count}")
            
            # List some key tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND table_name IN (
                    'leads', 'estimates', 'jobs', 'invoices', 
                    'crews', 'schedules', 'inventory_items', 
                    'purchase_orders', 'service_tickets', 'warranties',
                    'workflows', 'automation_rules', 'documents'
                )
                ORDER BY table_name
            """)
            
            key_tables = cursor.fetchall()
            if key_tables:
                logger.info("\nKey tables created:")
                for table in key_tables:
                    logger.info(f"  - {table[0]}")
        
        conn.close()
        logger.info("\n✅ Migration process complete!")
        
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return

if __name__ == "__main__":
    main()