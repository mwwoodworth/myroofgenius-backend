#!/usr/bin/env python3
"""
BrainOps Centerpoint ETL Pipeline
Version: 1.0.0
Complete data synchronization from Centerpoint systems
"""

import os
import json
import asyncio
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import httpx
import pandas as pd
from decimal import Decimal

# Database configuration
DB_CONFIG = {
    'host': 'aws-0-us-east-2.pooler.supabase.com',
    'port': 6543,
    'database': 'postgres',
    'user': 'postgres.yomagoqdmxszqtdwuhab',
    'password': '<DB_PASSWORD_REDACTED>'
}

# Centerpoint API configuration (placeholder - update with real endpoints)
CENTERPOINT_CONFIG = {
    'base_url': os.getenv('CENTERPOINT_API_URL', 'https://api.centerpoint.com'),
    'api_key': os.getenv('CENTERPOINT_API_KEY', ''),
    'sources': {
        'customers': '/api/v1/customers',
        'jobs': '/api/v1/jobs',
        'invoices': '/api/v1/invoices',
        'payments': '/api/v1/payments',
        'inventory': '/api/v1/inventory',
        'employees': '/api/v1/employees'
    }
}

class CenterpointETL:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.ingestion_id = str(uuid4())
        self.stats = {
            'total_records': 0,
            'processed_records': 0,
            'failed_records': 0,
            'start_time': datetime.utcnow()
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()
        if self.conn:
            self.conn.close()
    
    async def extract_data(self, source_name: str, endpoint: str) -> List[Dict]:
        """Extract data from Centerpoint API"""
        try:
            headers = {
                'Authorization': f'Bearer {CENTERPOINT_CONFIG["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            all_data = []
            page = 1
            has_more = True
            
            while has_more:
                response = await self.http_client.get(
                    f"{CENTERPOINT_CONFIG['base_url']}{endpoint}",
                    headers=headers,
                    params={'page': page, 'limit': 100}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    records = data.get('data', [])
                    all_data.extend(records)
                    
                    has_more = data.get('has_more', False)
                    page += 1
                else:
                    print(f"Error fetching {source_name}: {response.status_code}")
                    has_more = False
            
            print(f"Extracted {len(all_data)} records from {source_name}")
            return all_data
            
        except Exception as e:
            print(f"Extract error for {source_name}: {e}")
            return []
    
    def transform_customer(self, raw_data: Dict) -> Dict:
        """Transform customer data to our schema"""
        return {
            'external_id': f"CP-{raw_data.get('id', '')}",
            'name': raw_data.get('name', ''),
            'email': raw_data.get('email'),
            'phone': raw_data.get('phone'),
            'address': raw_data.get('address'),
            'city': raw_data.get('city'),
            'state': raw_data.get('state'),
            'zip_code': raw_data.get('zip'),
            'customer_type': raw_data.get('type', 'residential'),
            'status': 'active' if raw_data.get('active', True) else 'inactive',
            'metadata': json.dumps({
                'source': 'centerpoint',
                'original_id': raw_data.get('id'),
                'import_date': datetime.utcnow().isoformat()
            }),
            'created_at': raw_data.get('created_at', datetime.utcnow().isoformat()),
            'updated_at': datetime.utcnow()
        }
    
    def transform_job(self, raw_data: Dict) -> Dict:
        """Transform job data to our schema"""
        return {
            'job_number': f"CP-JOB-{raw_data.get('id', '')}",
            'customer_id': None,  # Will be mapped later
            'external_customer_id': f"CP-{raw_data.get('customer_id', '')}",
            'name': raw_data.get('title', ''),
            'description': raw_data.get('description'),
            'status': self._map_job_status(raw_data.get('status', 'pending')),
            'priority': raw_data.get('priority', 'medium'),
            'start_date': raw_data.get('start_date'),
            'end_date': raw_data.get('end_date'),
            'estimated_hours': raw_data.get('estimated_hours'),
            'actual_hours': raw_data.get('actual_hours'),
            'metadata': json.dumps({
                'source': 'centerpoint',
                'original_id': raw_data.get('id'),
                'import_date': datetime.utcnow().isoformat()
            }),
            'created_at': raw_data.get('created_at', datetime.utcnow().isoformat()),
            'updated_at': datetime.utcnow()
        }
    
    def _map_job_status(self, centerpoint_status: str) -> str:
        """Map Centerpoint status to our status"""
        status_map = {
            'new': 'pending',
            'in_progress': 'in_progress',
            'completed': 'completed',
            'cancelled': 'cancelled',
            'on_hold': 'on_hold'
        }
        return status_map.get(centerpoint_status.lower(), 'pending')
    
    def load_to_staging(self, table_name: str, data: List[Dict]) -> int:
        """Load data to staging tables"""
        if not data:
            return 0
        
        cursor = self.conn.cursor()
        staging_table = f"staging_{table_name}"
        
        # Create staging table if not exists
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {staging_table} (
                id SERIAL PRIMARY KEY,
                data JSONB NOT NULL,
                ingestion_id VARCHAR(255) NOT NULL,
                processed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Insert data
        values = [(json.dumps(record), self.ingestion_id) for record in data]
        execute_batch(
            cursor,
            f"INSERT INTO {staging_table} (data, ingestion_id) VALUES (%s, %s)",
            values
        )
        
        self.conn.commit()
        cursor.close()
        return len(data)
    
    def apply_mappings(self, source_table: str, target_table: str):
        """Apply transformation mappings from staging to target"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get mapping rules
        cursor.execute("""
            SELECT * FROM data.centerpoint_mappings 
            WHERE source_table = %s AND target_table = %s AND is_active = true
        """, (source_table, target_table))
        
        mappings = cursor.fetchall()
        
        # Process staged data
        staging_table = f"staging_{source_table}"
        cursor.execute(f"""
            SELECT * FROM {staging_table} 
            WHERE ingestion_id = %s AND processed = FALSE
        """, (self.ingestion_id,))
        
        staged_records = cursor.fetchall()
        
        for record in staged_records:
            transformed = self._apply_record_mapping(record['data'], mappings)
            
            # Insert or update target record
            self._upsert_record(target_table, transformed)
            
            # Mark as processed
            cursor.execute(f"""
                UPDATE {staging_table} SET processed = TRUE 
                WHERE id = %s
            """, (record['id'],))
        
        self.conn.commit()
        cursor.close()
    
    def _apply_record_mapping(self, data: Dict, mappings: List[Dict]) -> Dict:
        """Apply mapping rules to a single record"""
        result = {}
        
        for mapping in mappings:
            source_value = data.get(mapping['source_column'])
            
            if mapping['transform_function']:
                # Apply transformation function (eval is dangerous, use cautiously)
                # In production, use a safe expression evaluator
                try:
                    transformed = eval(mapping['transform_function'], 
                                     {'value': source_value, 'data': data})
                    result[mapping['target_column']] = transformed
                except:
                    result[mapping['target_column']] = source_value
            else:
                result[mapping['target_column']] = source_value
        
        return result
    
    def _upsert_record(self, table: str, data: Dict):
        """Insert or update a record"""
        cursor = self.conn.cursor()
        
        columns = list(data.keys())
        values = list(data.values())
        
        # Build INSERT ... ON CONFLICT UPDATE query
        insert_query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(['%s'] * len(columns))})
            ON CONFLICT (external_id) DO UPDATE SET
            {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'external_id'])}
        """
        
        cursor.execute(insert_query, values)
        cursor.close()
    
    def reconcile_data(self, entity_type: str):
        """Reconcile data between source and target"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get counts
        cursor.execute(f"""
            SELECT 
                (SELECT COUNT(*) FROM staging_{entity_type} WHERE ingestion_id = %s) as source_count,
                (SELECT COUNT(*) FROM {entity_type} WHERE external_id LIKE 'CP-%') as target_count
        """, (self.ingestion_id,))
        
        counts = cursor.fetchone()
        
        # Find discrepancies
        cursor.execute(f"""
            SELECT s.data->>'id' as source_id
            FROM staging_{entity_type} s
            WHERE ingestion_id = %s
            AND NOT EXISTS (
                SELECT 1 FROM {entity_type} t 
                WHERE t.external_id = 'CP-' || (s.data->>'id')
            )
        """, (self.ingestion_id,))
        
        unmatched = cursor.fetchall()
        
        # Store reconciliation record
        cursor.execute("""
            INSERT INTO data.centerpoint_reconciliations
            (reconciliation_date, source_system, target_system, entity_type,
             source_count, target_count, matched_count, unmatched_source, unmatched_target,
             discrepancies, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datetime.utcnow().date(),
            'centerpoint',
            'brainops',
            entity_type,
            counts['source_count'],
            counts['target_count'],
            counts['target_count'],
            len(unmatched),
            0,
            json.dumps([{'source_id': r['source_id']} for r in unmatched]),
            'balanced' if len(unmatched) == 0 else 'imbalanced'
        ))
        
        self.conn.commit()
        cursor.close()
        
        return {
            'source_count': counts['source_count'],
            'target_count': counts['target_count'],
            'unmatched': len(unmatched),
            'status': 'balanced' if len(unmatched) == 0 else 'imbalanced'
        }
    
    def track_lineage(self, entity_type: str, entity_id: str, source_id: str):
        """Track data lineage"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO data.centerpoint_lineage
            (entity_type, entity_id, source_system, source_id, ingestion_id)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (entity_type, entity_id, source_system, source_id) 
            DO UPDATE SET ingestion_id = EXCLUDED.ingestion_id
        """, (entity_type, entity_id, 'centerpoint', source_id, self.ingestion_id))
        
        self.conn.commit()
        cursor.close()
    
    def update_ingestion_status(self, status: str, error: Optional[str] = None):
        """Update ingestion record"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE data.centerpoint_ingestions
            SET status = %s,
                processed_records = %s,
                failed_records = %s,
                end_time = %s,
                error_log = %s
            WHERE ingestion_id = %s
        """, (
            status,
            self.stats['processed_records'],
            self.stats['failed_records'],
            datetime.utcnow(),
            error,
            self.ingestion_id
        ))
        
        self.conn.commit()
        cursor.close()
    
    def create_source_record(self, source_name: str, source_type: str, endpoint: str):
        """Create or update source configuration"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO data.centerpoint_sources
            (source_name, source_type, connection_string, sync_frequency_minutes)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (source_name) DO UPDATE 
            SET connection_string = EXCLUDED.connection_string,
                updated_at = NOW()
        """, (source_name, source_type, endpoint, 60))
        
        self.conn.commit()
        cursor.close()
    
    def start_ingestion(self, source_name: str) -> str:
        """Start a new ingestion"""
        cursor = self.conn.cursor()
        
        # Get source ID
        cursor.execute("""
            SELECT id FROM data.centerpoint_sources WHERE source_name = %s
        """, (source_name,))
        
        source = cursor.fetchone()
        if not source:
            self.create_source_record(source_name, 'api', CENTERPOINT_CONFIG['sources'].get(source_name, ''))
            cursor.execute("""
                SELECT id FROM data.centerpoint_sources WHERE source_name = %s
            """, (source_name,))
            source = cursor.fetchone()
        
        # Create ingestion record
        cursor.execute("""
            INSERT INTO data.centerpoint_ingestions
            (source_id, ingestion_id, status, total_records, start_time)
            VALUES (%s, %s, %s, %s, %s)
        """, (source[0], self.ingestion_id, 'running', 0, datetime.utcnow()))
        
        self.conn.commit()
        cursor.close()
        
        return self.ingestion_id
    
    async def sync_entity(self, entity_type: str):
        """Sync a specific entity type"""
        print(f"\n{'='*60}")
        print(f"Syncing {entity_type}...")
        print(f"{'='*60}")
        
        # Start ingestion
        self.start_ingestion(entity_type)
        
        # Extract
        endpoint = CENTERPOINT_CONFIG['sources'].get(entity_type)
        if not endpoint:
            print(f"No endpoint configured for {entity_type}")
            return
        
        raw_data = await self.extract_data(entity_type, endpoint)
        self.stats['total_records'] = len(raw_data)
        
        # Transform
        transformed_data = []
        for record in raw_data:
            try:
                if entity_type == 'customers':
                    transformed = self.transform_customer(record)
                elif entity_type == 'jobs':
                    transformed = self.transform_job(record)
                else:
                    transformed = record  # Use raw for others
                
                transformed_data.append(transformed)
                self.stats['processed_records'] += 1
            except Exception as e:
                print(f"Transform error: {e}")
                self.stats['failed_records'] += 1
        
        # Load to staging
        loaded = self.load_to_staging(entity_type, transformed_data)
        print(f"Loaded {loaded} records to staging")
        
        # Apply mappings
        self.apply_mappings(entity_type, entity_type)
        
        # Reconcile
        reconciliation = self.reconcile_data(entity_type)
        print(f"Reconciliation: {reconciliation}")
        
        # Update status
        self.update_ingestion_status('completed' if self.stats['failed_records'] == 0 else 'partial')
        
        print(f"Sync completed: {self.stats['processed_records']}/{self.stats['total_records']} processed")
    
    async def run_full_sync(self):
        """Run full synchronization for all entities"""
        entities = ['customers', 'jobs', 'invoices', 'payments', 'inventory', 'employees']
        
        for entity in entities:
            await self.sync_entity(entity)
            # Reset stats for next entity
            self.stats = {
                'total_records': 0,
                'processed_records': 0,
                'failed_records': 0,
                'start_time': datetime.utcnow()
            }
            self.ingestion_id = str(uuid4())
        
        print("\n" + "="*60)
        print("FULL SYNC COMPLETED")
        print("="*60)
    
    def generate_sync_report(self) -> Dict:
        """Generate sync report"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get recent ingestions
        cursor.execute("""
            SELECT 
                s.source_name,
                i.status,
                i.total_records,
                i.processed_records,
                i.failed_records,
                i.start_time,
                i.end_time
            FROM data.centerpoint_ingestions i
            JOIN data.centerpoint_sources s ON i.source_id = s.id
            WHERE i.start_time > NOW() - INTERVAL '24 hours'
            ORDER BY i.start_time DESC
        """)
        
        ingestions = cursor.fetchall()
        
        # Get reconciliation summary
        cursor.execute("""
            SELECT 
                entity_type,
                COUNT(*) as reconciliation_count,
                SUM(CASE WHEN status = 'balanced' THEN 1 ELSE 0 END) as balanced_count,
                SUM(unmatched_source + unmatched_target) as total_discrepancies
            FROM data.centerpoint_reconciliations
            WHERE reconciliation_date = CURRENT_DATE
            GROUP BY entity_type
        """)
        
        reconciliations = cursor.fetchall()
        
        cursor.close()
        
        return {
            'report_date': datetime.utcnow().isoformat(),
            'ingestions': ingestions,
            'reconciliations': reconciliations,
            'summary': {
                'total_ingestions': len(ingestions),
                'successful': sum(1 for i in ingestions if i['status'] == 'completed'),
                'failed': sum(1 for i in ingestions if i['status'] == 'failed'),
                'partial': sum(1 for i in ingestions if i['status'] == 'partial')
            }
        }

# Scheduler for automated sync
class CenterpointScheduler:
    def __init__(self):
        self.etl = None
    
    async def run_scheduled_sync(self):
        """Run scheduled sync"""
        while True:
            try:
                async with CenterpointETL() as etl:
                    self.etl = etl
                    await etl.run_full_sync()
                    
                    # Generate and store report
                    report = etl.generate_sync_report()
                    print(f"\nSync Report: {json.dumps(report, indent=2, default=str)}")
                
                # Wait for next sync (1 hour)
                await asyncio.sleep(3600)
                
            except Exception as e:
                print(f"Scheduler error: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes

# CLI interface
async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Centerpoint ETL Pipeline')
    parser.add_argument('--sync', choices=['full', 'customers', 'jobs', 'invoices'], 
                       help='Run sync for specific entity or full')
    parser.add_argument('--schedule', action='store_true', 
                       help='Run scheduled sync')
    parser.add_argument('--report', action='store_true',
                       help='Generate sync report')
    
    args = parser.parse_args()
    
    if args.schedule:
        scheduler = CenterpointScheduler()
        await scheduler.run_scheduled_sync()
    elif args.sync:
        async with CenterpointETL() as etl:
            if args.sync == 'full':
                await etl.run_full_sync()
            else:
                await etl.sync_entity(args.sync)
    elif args.report:
        async with CenterpointETL() as etl:
            report = etl.generate_sync_report()
            print(json.dumps(report, indent=2, default=str))
    else:
        # Default: run full sync once
        async with CenterpointETL() as etl:
            await etl.run_full_sync()

if __name__ == "__main__":
    asyncio.run(main())