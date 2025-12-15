"""
Database Master Monitor for Supabase
Comprehensive monitoring for 322+ tables with performance optimization
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMasterMonitor:
    def __init__(self):
        # Direct connection to master DB (not pooler)
        self.master_conn_str = "postgresql://postgres:<DB_PASSWORD_REDACTED>@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres"
        # Pooler connection for regular queries
        self.pooler_conn_str = "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
        
    def connect_master(self):
        """Connect to master database for full visibility"""
        return psycopg2.connect(self.master_conn_str, cursor_factory=RealDictCursor)
    
    def connect_pooler(self):
        """Connect via pooler for regular operations"""
        return psycopg2.connect(self.pooler_conn_str, cursor_factory=RealDictCursor)
    
    def get_database_overview(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        conn = self.connect_master()
        cur = conn.cursor()
        
        try:
            # Count tables
            cur.execute("""
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            table_count = cur.fetchone()['table_count']
            
            # Database size
            cur.execute("""
                SELECT pg_database_size('postgres') / 1024 / 1024 as size_mb
            """)
            db_size = cur.fetchone()['size_mb']
            
            # Connection stats
            cur.execute("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active,
                    count(*) FILTER (WHERE state = 'idle') as idle,
                    count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
                FROM pg_stat_activity
                WHERE datname = 'postgres'
            """)
            connections = cur.fetchone()
            
            # Cache hit ratio
            cur.execute("""
                SELECT 
                    sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100 as cache_hit_ratio
                FROM pg_statio_user_tables
            """)
            cache_hit = cur.fetchone()['cache_hit_ratio'] or 0
            
            return {
                "table_count": table_count,
                "database_size_mb": db_size,
                "connections": connections,
                "cache_hit_ratio": float(cache_hit),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            cur.close()
            conn.close()
    
    def identify_slow_queries(self, duration_ms: int = 1000) -> List[Dict]:
        """Identify slow queries"""
        conn = self.connect_master()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT 
                    pid,
                    now() - pg_stat_activity.query_start AS duration,
                    query,
                    state,
                    application_name,
                    client_addr
                FROM pg_stat_activity
                WHERE (now() - pg_stat_activity.query_start) > interval '%s milliseconds'
                AND state != 'idle'
                AND query NOT ILIKE '%%pg_stat_activity%%'
                ORDER BY duration DESC
                LIMIT 20
            """, (duration_ms,))
            
            slow_queries = []
            for row in cur.fetchall():
                slow_queries.append({
                    "pid": row['pid'],
                    "duration": str(row['duration']),
                    "query": row['query'][:500],  # Truncate long queries
                    "state": row['state'],
                    "application": row['application_name'],
                    "client": str(row['client_addr'])
                })
            
            return slow_queries
            
        finally:
            cur.close()
            conn.close()
    
    def get_table_statistics(self, limit: int = 50) -> List[Dict]:
        """Get statistics for largest/most active tables"""
        conn = self.connect_master()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
                    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes,
                    n_live_tup AS row_count,
                    n_dead_tup AS dead_rows,
                    n_tup_ins AS inserts,
                    n_tup_upd AS updates,
                    n_tup_del AS deletes,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT %s
            """, (limit,))
            
            tables = []
            for row in cur.fetchall():
                tables.append({
                    "table": row['tablename'],
                    "size": row['total_size'],
                    "size_bytes": row['size_bytes'],
                    "row_count": row['row_count'],
                    "dead_rows": row['dead_rows'],
                    "activity": {
                        "inserts": row['inserts'],
                        "updates": row['updates'],
                        "deletes": row['deletes']
                    },
                    "maintenance": {
                        "last_vacuum": row['last_vacuum'].isoformat() if row['last_vacuum'] else None,
                        "last_autovacuum": row['last_autovacuum'].isoformat() if row['last_autovacuum'] else None,
                        "last_analyze": row['last_analyze'].isoformat() if row['last_analyze'] else None
                    }
                })
            
            return tables
            
        finally:
            cur.close()
            conn.close()
    
    def identify_missing_indexes(self) -> List[Dict]:
        """Identify tables that might benefit from indexes"""
        conn = self.connect_master()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch,
                    CASE 
                        WHEN seq_scan > 0 THEN 
                            ROUND(100.0 * seq_scan / (seq_scan + idx_scan), 2)
                        ELSE 0 
                    END AS seq_scan_ratio
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                    AND seq_scan > 1000
                    AND seq_tup_read > 100000
                ORDER BY seq_tup_read DESC
                LIMIT 20
            """)
            
            tables_need_indexes = []
            for row in cur.fetchall():
                if row['seq_scan_ratio'] > 50:  # More than 50% sequential scans
                    tables_need_indexes.append({
                        "table": row['tablename'],
                        "seq_scans": row['seq_scan'],
                        "seq_rows_read": row['seq_tup_read'],
                        "index_scans": row['idx_scan'] or 0,
                        "seq_scan_ratio": float(row['seq_scan_ratio']),
                        "recommendation": "Consider adding indexes to reduce sequential scans"
                    })
            
            return tables_need_indexes
            
        finally:
            cur.close()
            conn.close()
    
    def check_table_bloat(self) -> List[Dict]:
        """Check for table bloat (dead tuples)"""
        conn = self.connect_master()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    n_live_tup,
                    n_dead_tup,
                    CASE 
                        WHEN n_live_tup > 0 THEN 
                            ROUND(100.0 * n_dead_tup / n_live_tup, 2)
                        ELSE 0 
                    END AS dead_tuple_ratio,
                    last_autovacuum
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                    AND n_dead_tup > 1000
                ORDER BY n_dead_tup DESC
                LIMIT 20
            """)
            
            bloated_tables = []
            for row in cur.fetchall():
                if row['dead_tuple_ratio'] > 10:  # More than 10% dead tuples
                    bloated_tables.append({
                        "table": row['tablename'],
                        "live_rows": row['n_live_tup'],
                        "dead_rows": row['n_dead_tup'],
                        "bloat_ratio": float(row['dead_tuple_ratio']),
                        "last_autovacuum": row['last_autovacuum'].isoformat() if row['last_autovacuum'] else None,
                        "recommendation": "Table needs VACUUM to reclaim space"
                    })
            
            return bloated_tables
            
        finally:
            cur.close()
            conn.close()
    
    def get_replication_status(self) -> Dict:
        """Check replication lag for read replicas"""
        conn = self.connect_master()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT 
                    client_addr,
                    state,
                    sent_lsn,
                    write_lsn,
                    flush_lsn,
                    replay_lsn,
                    write_lag,
                    flush_lag,
                    replay_lag,
                    sync_state
                FROM pg_stat_replication
            """)
            
            replicas = []
            for row in cur.fetchall():
                replicas.append({
                    "client": str(row['client_addr']),
                    "state": row['state'],
                    "write_lag": str(row['write_lag']) if row['write_lag'] else "0",
                    "flush_lag": str(row['flush_lag']) if row['flush_lag'] else "0",
                    "replay_lag": str(row['replay_lag']) if row['replay_lag'] else "0",
                    "sync_state": row['sync_state']
                })
            
            return {
                "replica_count": len(replicas),
                "replicas": replicas
            }
            
        finally:
            cur.close()
            conn.close()
    
    def optimize_database(self) -> Dict[str, Any]:
        """Run optimization commands"""
        conn = self.connect_master()
        cur = conn.cursor()
        optimizations = []
        
        try:
            # VACUUM ANALYZE on most active tables
            cur.execute("""
                SELECT tablename 
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public' 
                    AND (n_tup_ins + n_tup_upd + n_tup_del) > 10000
                ORDER BY (n_tup_ins + n_tup_upd + n_tup_del) DESC
                LIMIT 10
            """)
            
            tables_to_vacuum = [row['tablename'] for row in cur.fetchall()]
            
            for table in tables_to_vacuum:
                try:
                    cur.execute(f"VACUUM ANALYZE {table}")
                    conn.commit()
                    optimizations.append(f"✅ VACUUM ANALYZE on {table}")
                except Exception as e:
                    optimizations.append(f"❌ Failed to VACUUM {table}: {str(e)}")
            
            # Update statistics
            cur.execute("ANALYZE")
            conn.commit()
            optimizations.append("✅ Updated database statistics")
            
            return {
                "status": "completed",
                "optimizations": optimizations,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "optimizations": optimizations
            }
        finally:
            cur.close()
            conn.close()
    
    def generate_health_report(self) -> Dict:
        """Generate comprehensive health report"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overview": self.get_database_overview(),
            "slow_queries": self.identify_slow_queries(),
            "table_statistics": self.get_table_statistics(20),
            "missing_indexes": self.identify_missing_indexes(),
            "table_bloat": self.check_table_bloat(),
            "replication": self.get_replication_status(),
            "issues_found": 0,
            "recommendations": []
        }
        
        # Count issues
        issues = 0
        recommendations = []
        
        if report['slow_queries']:
            issues += len(report['slow_queries'])
            recommendations.append(f"Found {len(report['slow_queries'])} slow queries that need optimization")
        
        if report['missing_indexes']:
            issues += len(report['missing_indexes'])
            recommendations.append(f"Found {len(report['missing_indexes'])} tables that need indexes")
        
        if report['table_bloat']:
            issues += len(report['table_bloat'])
            recommendations.append(f"Found {len(report['table_bloat'])} tables with significant bloat")
        
        if report['overview']['cache_hit_ratio'] < 90:
            issues += 1
            recommendations.append(f"Cache hit ratio is {report['overview']['cache_hit_ratio']:.1f}% - consider increasing shared_buffers")
        
        report['issues_found'] = issues
        report['recommendations'] = recommendations
        
        return report

def main():
    """Run comprehensive database monitoring"""
    monitor = DatabaseMasterMonitor()
    
    print("🔍 Database Master Monitor")
    print("=" * 60)
    
    # Generate health report
    report = monitor.generate_health_report()
    
    print(f"\n📊 Database Overview:")
    print(f"  Tables: {report['overview']['table_count']}")
    print(f"  Size: {report['overview']['database_size_mb']:.1f} MB")
    print(f"  Connections: {report['overview']['connections']['active']} active, {report['overview']['connections']['idle']} idle")
    print(f"  Cache Hit Ratio: {report['overview']['cache_hit_ratio']:.1f}%")
    
    print(f"\n⚠️  Issues Found: {report['issues_found']}")
    for rec in report['recommendations']:
        print(f"  - {rec}")
    
    if report['slow_queries']:
        print(f"\n🐌 Slow Queries ({len(report['slow_queries'])}):")
        for q in report['slow_queries'][:3]:
            print(f"  - Duration: {q['duration']}")
            print(f"    Query: {q['query'][:100]}...")
    
    if report['missing_indexes']:
        print(f"\n📑 Tables Needing Indexes ({len(report['missing_indexes'])}):")
        for t in report['missing_indexes'][:5]:
            print(f"  - {t['table']}: {t['seq_scan_ratio']:.1f}% sequential scans")
    
    if report['table_bloat']:
        print(f"\n💾 Bloated Tables ({len(report['table_bloat'])}):")
        for t in report['table_bloat'][:5]:
            print(f"  - {t['table']}: {t['bloat_ratio']:.1f}% dead tuples")
    
    # Ask to optimize
    print("\n" + "=" * 60)
    response = input("Run optimization? (y/n): ")
    if response.lower() == 'y':
        print("\n🔧 Running optimizations...")
        result = monitor.optimize_database()
        for opt in result['optimizations']:
            print(f"  {opt}")
    
    # Save report
    with open('/home/mwwoodworth/code/database_health_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n📄 Full report saved to database_health_report.json")

if __name__ == "__main__":
    main()