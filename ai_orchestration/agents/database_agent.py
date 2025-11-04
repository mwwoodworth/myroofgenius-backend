"""
DatabaseAgent - Master of the Database
Manages, monitors, optimizes, and maintains the production database.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncpg
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core import Agent, MemoryType, MessageType, SystemComponent

logger = logging.getLogger(__name__)

class DatabaseAgent(Agent):
    """
    The database guardian who ensures data integrity, performance, and availability.
    Manages all aspects of the Supabase PostgreSQL database.
    """
    
    def __init__(self):
        super().__init__(
            name="DatabaseAgent",
            specialization="database_management",
            capabilities=[
                "schema_management",
                "performance_optimization",
                "backup_verification",
                "data_integrity_checks",
                "index_optimization",
                "query_analysis",
                "table_maintenance",
                "connection_monitoring",
                "replication_status",
                "centerpoint_data_protection"
            ]
        )
        
        # Database knowledge
        self.critical_tables = [
            'centerpoint_companies',
            'centerpoint_files',
            'centerpoint_data',
            'customers',
            'jobs',
            'ai_agents',
            'agent_registry',
            'agent_memory'
        ]
        
        self.centerpoint_tables = [
            'centerpoint_cache', 'centerpoint_communications', 'centerpoint_companies',
            'centerpoint_contacts', 'centerpoint_data', 'centerpoint_employees',
            'centerpoint_equipment', 'centerpoint_estimates', 'centerpoint_files',
            'centerpoint_invoices', 'centerpoint_job_history', 'centerpoint_notes',
            'centerpoint_photos', 'centerpoint_productions', 'centerpoint_products',
            'centerpoint_raw_data', 'centerpoint_sync_data', 'centerpoint_sync_log',
            'centerpoint_sync_status', 'centerpoint_tickets', 'centerpoint_users',
            'cp_download_jobs', 'cp_entity_sync', 'cp_file_blobs', 'cp_file_content',
            'cp_file_integrity', 'cp_file_large_objects', 'cp_file_queue', 'cp_file_storage',
            'cp_files_manifest', 'cp_final_companies', 'cp_final_invoices', 'cp_final_productions',
            'cp_final_properties', 'cp_final_transactions', 'cp_final_warranties',
            'cp_production_warranties', 'cp_storage_migrations', 'cp_sync_companies',
            'cp_sync_status', 'cp_sync_tracking'
        ]
        
        self.performance_thresholds = {
            'query_time_warning': 1.0,  # seconds
            'query_time_critical': 5.0,
            'connection_limit': 90,  # percentage
            'disk_usage_warning': 80,  # percentage
            'disk_usage_critical': 90,
            'table_bloat_warning': 20,  # percentage
            'index_bloat_warning': 30
        }
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Comprehensive database health check
        """
        health_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'connection': {},
            'performance': {},
            'storage': {},
            'tables': {},
            'indexes': {},
            'replication': {},
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Check connection
            health_report['connection'] = await self._check_connection()
            
            # Check performance
            health_report['performance'] = await self._check_performance()
            
            # Check storage
            health_report['storage'] = await self._check_storage()
            
            # Check tables
            health_report['tables'] = await self._check_tables()
            
            # Check indexes
            health_report['indexes'] = await self._check_indexes()
            
            # Check CenterPoint data integrity
            health_report['centerpoint'] = await self._check_centerpoint_integrity()
            
            # Analyze issues
            health_report['issues'] = self._analyze_issues(health_report)
            
            # Generate recommendations
            health_report['recommendations'] = self._generate_recommendations(health_report)
            
            # Determine overall status
            if health_report['issues']:
                critical_issues = [i for i in health_report['issues'] if i.get('severity') == 'critical']
                if critical_issues:
                    health_report['overall_status'] = 'critical'
                else:
                    health_report['overall_status'] = 'warning'
            
            # Store in memory
            await self.memory.remember(
                MemoryType.KNOWLEDGE,
                health_report,
                relevance=1.0
            )
            
            # Update system state
            await self._update_system_state(health_report)
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_report['overall_status'] = 'error'
            health_report['error'] = str(e)
            
            # Remember the error
            await self.memory.remember(
                MemoryType.ERROR,
                {
                    'action': 'health_check',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        
        return health_report
    
    async def _check_connection(self) -> Dict[str, Any]:
        """Check database connectivity"""
        connection_info = {
            'connected': False,
            'connection_count': 0,
            'max_connections': 0,
            'connection_usage': 0,
            'response_time': None
        }
        
        try:
            start_time = datetime.utcnow()
            
            async with self.pool.acquire() as conn:
                # Test connection
                await conn.fetchval("SELECT 1")
                connection_info['connected'] = True
                connection_info['response_time'] = (datetime.utcnow() - start_time).total_seconds()
                
                # Get connection stats
                stats = await conn.fetchrow("""
                    SELECT 
                        (SELECT count(*) FROM pg_stat_activity) as current_connections,
                        (SELECT setting FROM pg_settings WHERE name = 'max_connections') as max_connections
                """)
                
                connection_info['connection_count'] = stats['current_connections']
                connection_info['max_connections'] = int(stats['max_connections'])
                connection_info['connection_usage'] = (stats['current_connections'] / int(stats['max_connections'])) * 100
        
        except Exception as e:
            connection_info['error'] = str(e)
        
        return connection_info
    
    async def _check_performance(self) -> Dict[str, Any]:
        """Check database performance metrics"""
        performance = {
            'slow_queries': [],
            'cache_hit_ratio': 0,
            'transaction_rate': 0,
            'deadlocks': 0,
            'temp_files': 0
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Get slow queries
                slow_queries = await conn.fetch("""
                    SELECT 
                        query,
                        calls,
                        mean_exec_time,
                        total_exec_time
                    FROM pg_stat_statements
                    WHERE mean_exec_time > $1
                    ORDER BY mean_exec_time DESC
                    LIMIT 10
                """, self.performance_thresholds['query_time_warning'] * 1000)
                
                performance['slow_queries'] = [
                    {
                        'query': q['query'][:100],
                        'calls': q['calls'],
                        'mean_time': q['mean_exec_time'],
                        'total_time': q['total_exec_time']
                    }
                    for q in slow_queries
                ]
                
                # Get cache hit ratio
                cache_stats = await conn.fetchrow("""
                    SELECT 
                        sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) as cache_hit_ratio
                    FROM pg_statio_user_tables
                """)
                performance['cache_hit_ratio'] = float(cache_stats['cache_hit_ratio'] or 0) * 100
                
                # Get transaction rate
                tx_stats = await conn.fetchrow("""
                    SELECT 
                        xact_commit + xact_rollback as transactions
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)
                performance['transaction_rate'] = tx_stats['transactions']
                
                # Get deadlock count
                deadlock_stats = await conn.fetchrow("""
                    SELECT deadlocks
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)
                performance['deadlocks'] = deadlock_stats['deadlocks']
        
        except Exception as e:
            performance['error'] = str(e)
        
        return performance
    
    async def _check_storage(self) -> Dict[str, Any]:
        """Check storage usage"""
        storage = {
            'database_size': 0,
            'table_sizes': {},
            'index_sizes': {},
            'temp_size': 0,
            'disk_usage_percent': 0
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Get database size
                db_size = await conn.fetchval("""
                    SELECT pg_database_size(current_database())
                """)
                storage['database_size'] = db_size
                
                # Get top 10 largest tables
                table_sizes = await conn.fetch("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_total_relation_size(schemaname||'.'||tablename) as size
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY size DESC
                    LIMIT 10
                """)
                
                storage['table_sizes'] = {
                    f"{t['schemaname']}.{t['tablename']}": t['size']
                    for t in table_sizes
                }
                
                # Get index sizes
                index_sizes = await conn.fetch("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        pg_relation_size(indexrelid) as size
                    FROM pg_stat_user_indexes
                    ORDER BY size DESC
                    LIMIT 10
                """)
                
                storage['index_sizes'] = {
                    idx['indexname']: idx['size']
                    for idx in index_sizes
                }
        
        except Exception as e:
            storage['error'] = str(e)
        
        return storage
    
    async def _check_tables(self) -> Dict[str, Any]:
        """Check table health"""
        tables = {
            'total_count': 0,
            'critical_tables_status': {},
            'bloated_tables': [],
            'missing_indexes': []
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Count tables
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)
                tables['total_count'] = count
                
                # Check critical tables
                for table in self.critical_tables:
                    try:
                        row_count = await conn.fetchval(f"""
                            SELECT COUNT(*) FROM {table}
                        """)
                        tables['critical_tables_status'][table] = {
                            'exists': True,
                            'row_count': row_count
                        }
                    except:
                        tables['critical_tables_status'][table] = {
                            'exists': False,
                            'row_count': 0
                        }
                
                # Check for bloated tables
                bloat_check = await conn.fetch("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        n_dead_tup,
                        n_live_tup,
                        CASE WHEN n_live_tup > 0 
                            THEN round(100.0 * n_dead_tup / n_live_tup, 2)
                            ELSE 0
                        END as bloat_percent
                    FROM pg_stat_user_tables
                    WHERE n_dead_tup > 1000
                    ORDER BY n_dead_tup DESC
                    LIMIT 10
                """)
                
                tables['bloated_tables'] = [
                    {
                        'table': f"{b['schemaname']}.{b['tablename']}",
                        'size': b['size'],
                        'dead_tuples': b['n_dead_tup'],
                        'bloat_percent': float(b['bloat_percent'])
                    }
                    for b in bloat_check
                    if float(b['bloat_percent']) > self.performance_thresholds['table_bloat_warning']
                ]
        
        except Exception as e:
            tables['error'] = str(e)
        
        return tables
    
    async def _check_indexes(self) -> Dict[str, Any]:
        """Check index health"""
        indexes = {
            'total_count': 0,
            'unused_indexes': [],
            'duplicate_indexes': [],
            'missing_indexes': []
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Count indexes
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM pg_indexes
                    WHERE schemaname = 'public'
                """)
                indexes['total_count'] = count
                
                # Find unused indexes
                unused = await conn.fetch("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        pg_size_pretty(pg_relation_size(indexrelid)) as size
                    FROM pg_stat_user_indexes
                    WHERE idx_scan = 0
                    AND indexrelname NOT LIKE '%_pkey'
                    ORDER BY pg_relation_size(indexrelid) DESC
                    LIMIT 10
                """)
                
                indexes['unused_indexes'] = [
                    {
                        'index': u['indexname'],
                        'table': f"{u['schemaname']}.{u['tablename']}",
                        'size': u['size']
                    }
                    for u in unused
                ]
                
                # Find duplicate indexes (simplified check)
                duplicates = await conn.fetch("""
                    WITH index_data AS (
                        SELECT 
                            schemaname,
                            tablename,
                            indexname,
                            indexdef,
                            pg_get_indexdef(indexrelid) as full_def
                        FROM pg_indexes
                        JOIN pg_stat_user_indexes USING (schemaname, tablename, indexname)
                        WHERE schemaname = 'public'
                    )
                    SELECT 
                        tablename,
                        array_agg(indexname) as duplicate_indexes
                    FROM index_data
                    GROUP BY tablename, replace(indexdef, indexname, 'INDEX_NAME')
                    HAVING COUNT(*) > 1
                """)
                
                if duplicates:
                    indexes['duplicate_indexes'] = [
                        {
                            'table': d['tablename'],
                            'indexes': d['duplicate_indexes']
                        }
                        for d in duplicates
                    ]
        
        except Exception as e:
            indexes['error'] = str(e)
        
        return indexes
    
    async def _check_centerpoint_integrity(self) -> Dict[str, Any]:
        """Check CenterPoint data integrity"""
        centerpoint = {
            'total_records': 0,
            'table_status': {},
            'data_quality': {},
            'sync_status': {}
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Check each CenterPoint table
                for table in self.centerpoint_tables:
                    try:
                        # Count records
                        count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                        
                        # Check for NULL critical fields (if applicable)
                        null_check = None
                        if 'companies' in table:
                            null_check = await conn.fetchval(f"""
                                SELECT COUNT(*) FROM {table}
                                WHERE centerpoint_id IS NULL OR data IS NULL
                            """)
                        
                        centerpoint['table_status'][table] = {
                            'exists': True,
                            'record_count': count,
                            'null_critical_fields': null_check or 0
                        }
                        
                        centerpoint['total_records'] += count
                        
                    except Exception as e:
                        centerpoint['table_status'][table] = {
                            'exists': False,
                            'error': str(e)
                        }
                
                # Check sync status
                sync_status = await conn.fetch("""
                    SELECT 
                        entity_type,
                        last_sync_at,
                        records_synced,
                        status
                    FROM centerpoint_sync_status
                    ORDER BY last_sync_at DESC
                    LIMIT 10
                """)
                
                centerpoint['sync_status'] = [
                    {
                        'entity': s['entity_type'],
                        'last_sync': s['last_sync_at'].isoformat() if s['last_sync_at'] else None,
                        'records': s['records_synced'],
                        'status': s['status']
                    }
                    for s in sync_status
                ]
        
        except Exception as e:
            centerpoint['error'] = str(e)
        
        return centerpoint
    
    async def optimize_database(self) -> Dict[str, Any]:
        """Run database optimization tasks"""
        optimization_result = {
            'timestamp': datetime.utcnow().isoformat(),
            'vacuum': {},
            'analyze': {},
            'reindex': {},
            'cleanup': {}
        }
        
        try:
            async with self.pool.acquire() as conn:
                # VACUUM bloated tables
                health = await self.check_health()
                bloated_tables = health.get('tables', {}).get('bloated_tables', [])
                
                for table_info in bloated_tables[:5]:  # Limit to top 5
                    table = table_info['table']
                    try:
                        await conn.execute(f"VACUUM ANALYZE {table}")
                        optimization_result['vacuum'][table] = 'success'
                    except Exception as e:
                        optimization_result['vacuum'][table] = str(e)
                
                # Update statistics on critical tables
                for table in self.critical_tables:
                    try:
                        await conn.execute(f"ANALYZE {table}")
                        optimization_result['analyze'][table] = 'success'
                    except Exception as e:
                        optimization_result['analyze'][table] = str(e)
                
                # Clean up old data (carefully)
                cleanup_queries = [
                    ("agent_communications", "DELETE FROM agent_communications WHERE created_at < NOW() - INTERVAL '30 days' AND processed = TRUE"),
                    ("system_events", "DELETE FROM system_events WHERE created_at < NOW() - INTERVAL '60 days' AND processed = TRUE"),
                    ("workflow_executions", "DELETE FROM workflow_executions WHERE completed_at < NOW() - INTERVAL '90 days'")
                ]
                
                for table, query in cleanup_queries:
                    try:
                        result = await conn.execute(query)
                        optimization_result['cleanup'][table] = result
                    except Exception as e:
                        optimization_result['cleanup'][table] = str(e)
            
            # Remember optimization
            await self.memory.remember(
                MemoryType.EXPERIENCE,
                {
                    'action': 'database_optimization',
                    'result': optimization_result,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        
        except Exception as e:
            optimization_result['error'] = str(e)
            
            await self.memory.remember(
                MemoryType.ERROR,
                {
                    'action': 'database_optimization',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        
        return optimization_result
    
    async def backup_verify(self) -> Dict[str, Any]:
        """Verify backup status"""
        backup_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'last_backup': None,
            'backup_size': None,
            'recovery_point': None,
            'verification': 'pending'
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Check for backup-related settings
                backup_info = await conn.fetch("""
                    SELECT name, setting 
                    FROM pg_settings 
                    WHERE name IN ('archive_mode', 'archive_command', 'wal_level')
                """)
                
                backup_status['settings'] = {
                    b['name']: b['setting']
                    for b in backup_info
                }
                
                # Check last checkpoint
                checkpoint = await conn.fetchrow("""
                    SELECT checkpoint_lsn, checkpoint_time
                    FROM pg_control_checkpoint()
                """)
                
                if checkpoint:
                    backup_status['recovery_point'] = checkpoint['checkpoint_time'].isoformat()
                
                backup_status['verification'] = 'success'
        
        except Exception as e:
            backup_status['error'] = str(e)
            backup_status['verification'] = 'failed'
        
        return backup_status
    
    def _analyze_issues(self, health_report: Dict) -> List[Dict]:
        """Analyze health report for issues"""
        issues = []
        
        # Connection issues
        conn = health_report.get('connection', {})
        if conn.get('connection_usage', 0) > self.performance_thresholds['connection_limit']:
            issues.append({
                'type': 'high_connection_usage',
                'severity': 'warning',
                'details': f"Connection usage at {conn['connection_usage']:.1f}%"
            })
        
        # Performance issues
        perf = health_report.get('performance', {})
        if perf.get('slow_queries'):
            issues.append({
                'type': 'slow_queries',
                'severity': 'warning',
                'count': len(perf['slow_queries']),
                'details': f"{len(perf['slow_queries'])} slow queries detected"
            })
        
        if perf.get('cache_hit_ratio', 100) < 90:
            issues.append({
                'type': 'low_cache_hit_ratio',
                'severity': 'warning',
                'details': f"Cache hit ratio: {perf['cache_hit_ratio']:.1f}%"
            })
        
        # Table issues
        tables = health_report.get('tables', {})
        if tables.get('bloated_tables'):
            issues.append({
                'type': 'table_bloat',
                'severity': 'warning',
                'count': len(tables['bloated_tables']),
                'details': f"{len(tables['bloated_tables'])} bloated tables"
            })
        
        # Index issues
        indexes = health_report.get('indexes', {})
        if indexes.get('unused_indexes'):
            issues.append({
                'type': 'unused_indexes',
                'severity': 'info',
                'count': len(indexes['unused_indexes']),
                'details': f"{len(indexes['unused_indexes'])} unused indexes"
            })
        
        # CenterPoint issues
        cp = health_report.get('centerpoint', {})
        for table, status in cp.get('table_status', {}).items():
            if not status.get('exists'):
                issues.append({
                    'type': 'missing_centerpoint_table',
                    'severity': 'critical',
                    'table': table,
                    'details': f"CenterPoint table {table} is missing"
                })
        
        return issues
    
    def _generate_recommendations(self, health_report: Dict) -> List[Dict]:
        """Generate recommendations based on health report"""
        recommendations = []
        
        issues = health_report.get('issues', [])
        
        for issue in issues:
            if issue['type'] == 'slow_queries':
                recommendations.append({
                    'priority': 'high',
                    'action': 'optimize_queries',
                    'description': 'Review and optimize slow queries',
                    'details': 'Run EXPLAIN ANALYZE on slow queries and add appropriate indexes'
                })
            
            elif issue['type'] == 'table_bloat':
                recommendations.append({
                    'priority': 'medium',
                    'action': 'vacuum_tables',
                    'description': 'Run VACUUM on bloated tables',
                    'details': f"Tables need vacuum: {issue.get('count', 0)} tables"
                })
            
            elif issue['type'] == 'unused_indexes':
                recommendations.append({
                    'priority': 'low',
                    'action': 'remove_unused_indexes',
                    'description': 'Consider removing unused indexes',
                    'details': 'Unused indexes consume space and slow down writes'
                })
            
            elif issue['type'] == 'low_cache_hit_ratio':
                recommendations.append({
                    'priority': 'high',
                    'action': 'increase_cache',
                    'description': 'Increase shared_buffers or optimize queries',
                    'details': 'Low cache hit ratio affects performance'
                })
            
            elif issue['type'] == 'missing_centerpoint_table':
                recommendations.append({
                    'priority': 'critical',
                    'action': 'restore_table',
                    'description': f"Restore missing table: {issue.get('table')}",
                    'details': 'Critical CenterPoint data table is missing'
                })
        
        return recommendations
    
    async def _update_system_state(self, health_report: Dict):
        """Update system state with database health"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO system_state (state_id, component, health_status, last_check, metrics, issues, agent_owner)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (component) DO UPDATE SET
                        health_status = $3,
                        last_check = $4,
                        metrics = $5,
                        issues = $6,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    str(uuid.uuid4()),
                    'database',
                    health_report['overall_status'],
                    datetime.utcnow(),
                    json.dumps({
                        'connection': health_report.get('connection'),
                        'performance': health_report.get('performance'),
                        'storage': health_report.get('storage')
                    }),
                    json.dumps(health_report.get('issues', [])),
                    self.agent_id
                )
        except Exception as e:
            logger.error(f"Failed to update system state: {e}")
    
    async def handle_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle queries from other agents"""
        query_type = query.get('type')
        
        if query_type == 'health_check':
            return await self.check_health()
        
        elif query_type == 'table_info':
            table = query.get('table')
            return await self._get_table_info(table)
        
        elif query_type == 'optimize':
            return await self.optimize_database()
        
        elif query_type == 'backup_status':
            return await self.backup_verify()
        
        elif query_type == 'centerpoint_status':
            health = await self.check_health()
            return health.get('centerpoint', {})
        
        elif query_type == 'run_query':
            # Only for safe SELECT queries
            sql = query.get('sql', '')
            if sql.upper().startswith('SELECT'):
                try:
                    async with self.pool.acquire() as conn:
                        result = await conn.fetch(sql)
                        return {'success': True, 'data': [dict(r) for r in result]}
                except Exception as e:
                    return {'success': False, 'error': str(e)}
            else:
                return {'success': False, 'error': 'Only SELECT queries allowed'}
        
        else:
            return {'error': f'Unknown query type: {query_type}'}
    
    async def _get_table_info(self, table: str) -> Dict[str, Any]:
        """Get detailed information about a table"""
        info = {
            'table': table,
            'exists': False,
            'columns': [],
            'indexes': [],
            'row_count': 0,
            'size': 0
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Check if table exists
                exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = $1
                    )
                """, table)
                
                if exists:
                    info['exists'] = True
                    
                    # Get columns
                    columns = await conn.fetch("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = $1
                        ORDER BY ordinal_position
                    """, table)
                    
                    info['columns'] = [
                        {
                            'name': c['column_name'],
                            'type': c['data_type'],
                            'nullable': c['is_nullable'] == 'YES'
                        }
                        for c in columns
                    ]
                    
                    # Get indexes
                    indexes = await conn.fetch("""
                        SELECT indexname, indexdef
                        FROM pg_indexes
                        WHERE schemaname = 'public' AND tablename = $1
                    """, table)
                    
                    info['indexes'] = [
                        {
                            'name': i['indexname'],
                            'definition': i['indexdef']
                        }
                        for i in indexes
                    ]
                    
                    # Get row count
                    info['row_count'] = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    
                    # Get size
                    info['size'] = await conn.fetchval(f"""
                        SELECT pg_total_relation_size('{table}')
                    """)
        
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    async def run(self):
        """Main agent loop"""
        await self.initialize()
        
        while True:
            try:
                # Periodic health check (every 10 minutes)
                await self.check_health()
                
                # Optimization (every hour)
                if datetime.utcnow().minute == 0:
                    await self.optimize_database()
                
                # Backup verification (every 6 hours)
                if datetime.utcnow().hour % 6 == 0 and datetime.utcnow().minute == 0:
                    await self.backup_verify()
                
                # Check for messages
                messages = await self.communication.receive(limit=10)
                
                for message in messages:
                    if message['message_type'] == MessageType.QUERY.value:
                        response = await self.handle_query(message['content'])
                        
                        await self.communication.send(
                            message['from_agent'],
                            MessageType.RESPONSE,
                            response
                        )
                    
                    elif message['message_type'] == MessageType.ALERT.value:
                        # Handle database-related alerts
                        alert = message['content']
                        
                        if alert.get('type') == 'slow_query':
                            # Analyze slow query
                            await self._analyze_slow_query(alert.get('query'))
                        
                        elif alert.get('type') == 'connection_spike':
                            # Check connection pool
                            health = await self.check_health()
                            if health['connection']['connection_usage'] > 90:
                                # Alert other agents
                                await self.communication.broadcast(
                                    MessageType.ALERT,
                                    {
                                        'type': 'database_connection_critical',
                                        'details': health['connection']
                                    },
                                    priority=1
                                )
                
                # Learn from experiences
                if datetime.utcnow().minute % 30 == 0:
                    await self.learn()
                
                # Sleep before next cycle
                await asyncio.sleep(60)  # 1 minute
                
            except Exception as e:
                logger.error(f"DatabaseAgent error: {e}")
                
                await self.memory.remember(
                    MemoryType.ERROR,
                    {
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
                await asyncio.sleep(60)

# Agent instance
database_agent = DatabaseAgent()