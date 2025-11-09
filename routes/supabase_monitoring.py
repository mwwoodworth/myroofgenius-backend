"""
Supabase Database Monitoring & Management Routes
Comprehensive monitoring for 322+ tables with performance optimization
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/v1/supabase",
    tags=["Supabase Monitoring"]
)

logger = logging.getLogger(__name__)

# Database connections
MASTER_DB_URL = ""
POOLER_DB_URL = ""

def get_master_connection():
    """Direct connection to master for full visibility"""
    return psycopg2.connect(MASTER_DB_URL, cursor_factory=RealDictCursor)

def get_pooler_connection():
    """Pooler connection for regular operations"""
    return psycopg2.connect(POOLER_DB_URL, cursor_factory=RealDictCursor)

# ============================================================================
# DATABASE OVERVIEW
# ============================================================================

@router.get("/overview")
async def get_database_overview():
    """Get comprehensive database statistics"""
    try:
        conn = get_master_connection()
        cur = conn.cursor()
        
        # Count all tables
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE table_type = 'BASE TABLE') as tables,
                COUNT(*) FILTER (WHERE table_type = 'VIEW') as views,
                COUNT(DISTINCT table_schema) as schemas
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        """)
        counts = cur.fetchone()
        
        # Database size
        cur.execute("""
            SELECT 
                pg_database_size('postgres') / 1024 / 1024 as size_mb,
                pg_database_size('postgres') / 1024 / 1024 / 1024 as size_gb
        """)
        size = cur.fetchone()
        
        # Connection pool stats
        cur.execute("""
            SELECT 
                max_connections,
                (SELECT count(*) FROM pg_stat_activity) as current_connections,
                (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_queries,
                (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle') as idle_connections,
                (SELECT count(*) FROM pg_stat_activity WHERE wait_event_type IS NOT NULL) as waiting_queries
            FROM 
                (SELECT setting::int as max_connections FROM pg_settings WHERE name = 'max_connections') s
        """)
        connections = cur.fetchone()
        
        # Performance metrics
        cur.execute("""
            SELECT 
                (SELECT sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100 
                 FROM pg_statio_user_tables) as cache_hit_ratio,
                (SELECT count(*) FROM pg_stat_user_tables WHERE n_dead_tup > 1000) as tables_need_vacuum,
                (SELECT count(*) FROM pg_stat_user_tables WHERE last_autovacuum < NOW() - INTERVAL '7 days') as stale_tables
        """)
        performance = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            "database": {
                "tables": counts['tables'],
                "views": counts['views'],
                "schemas": counts['schemas'],
                "size_mb": round(size['size_mb'], 2),
                "size_gb": round(size['size_gb'], 2)
            },
            "connections": {
                "max": connections['max_connections'],
                "current": connections['current_connections'],
                "active": connections['active_queries'],
                "idle": connections['idle_connections'],
                "waiting": connections['waiting_queries'],
                "usage_percent": round(connections['current_connections'] / connections['max_connections'] * 100, 2)
            },
            "performance": {
                "cache_hit_ratio": round(float(performance['cache_hit_ratio'] or 0), 2),
                "tables_need_vacuum": performance['tables_need_vacuum'],
                "stale_tables": performance['stale_tables']
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting database overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SLOW QUERY ANALYSIS
# ============================================================================

@router.get("/slow-queries")
async def get_slow_queries(
    duration_ms: int = 1000,
    limit: int = 20
):
    """Identify and analyze slow queries"""
    try:
        conn = get_master_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                pid,
                now() - pg_stat_activity.query_start AS duration,
                query,
                state,
                wait_event_type,
                wait_event,
                application_name,
                client_addr,
                usename
            FROM pg_stat_activity
            WHERE (now() - pg_stat_activity.query_start) > interval '%s milliseconds'
            AND state != 'idle'
            AND query NOT ILIKE '%%pg_stat_activity%%'
            ORDER BY duration DESC
            LIMIT %s
        """, (duration_ms, limit))
        
        slow_queries = []
        for row in cur.fetchall():
            slow_queries.append({
                "pid": row['pid'],
                "duration": str(row['duration']),
                "duration_ms": int(row['duration'].total_seconds() * 1000),
                "query": row['query'][:500],  # Truncate long queries
                "state": row['state'],
                "wait_event": f"{row['wait_event_type']}: {row['wait_event']}" if row['wait_event_type'] else None,
                "application": row['application_name'],
                "client": str(row['client_addr']),
                "user": row['usename']
            })
        
        # Get query statistics
        cur.execute("""
            SELECT 
                COUNT(*) as total_statements,
                SUM(calls) as total_calls,
                AVG(mean_exec_time) as avg_exec_time_ms,
                MAX(max_exec_time) as max_exec_time_ms,
                SUM(total_exec_time) / 1000 as total_time_seconds
            FROM pg_stat_statements
            WHERE query NOT LIKE '%pg_stat%'
        """)
        stats = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            "slow_queries": slow_queries,
            "statistics": {
                "total_statements": stats['total_statements'] if stats else 0,
                "total_calls": stats['total_calls'] if stats else 0,
                "avg_exec_time_ms": round(float(stats['avg_exec_time_ms'] or 0), 2),
                "max_exec_time_ms": round(float(stats['max_exec_time_ms'] or 0), 2),
                "total_time_seconds": round(float(stats['total_time_seconds'] or 0), 2)
            },
            "threshold_ms": duration_ms,
            "count": len(slow_queries)
        }
    except Exception as e:
        logger.error(f"Error getting slow queries: {e}")
        # pg_stat_statements might not be enabled
        if "pg_stat_statements" in str(e):
            return {
                "slow_queries": [],
                "statistics": {},
                "error": "pg_stat_statements extension not enabled",
                "recommendation": "Enable pg_stat_statements for detailed query analysis"
            }
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# TABLE ANALYSIS
# ============================================================================

@router.get("/tables/analysis")
async def analyze_tables(
    limit: int = 50,
    order_by: str = "size"  # size, activity, bloat
):
    """Analyze table statistics and health"""
    try:
        conn = get_master_connection()
        cur = conn.cursor()
        
        order_clause = {
            "size": "pg_total_relation_size(schemaname||'.'||tablename) DESC",
            "activity": "(n_tup_ins + n_tup_upd + n_tup_del) DESC",
            "bloat": "n_dead_tup DESC"
        }.get(order_by, "pg_total_relation_size(schemaname||'.'||tablename) DESC")
        
        cur.execute(f"""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes,
                n_live_tup AS live_rows,
                n_dead_tup AS dead_rows,
                CASE 
                    WHEN n_live_tup > 0 THEN 
                        ROUND(100.0 * n_dead_tup / n_live_tup, 2)
                    ELSE 0 
                END AS bloat_ratio,
                n_tup_ins AS inserts,
                n_tup_upd AS updates,
                n_tup_del AS deletes,
                n_tup_hot_upd AS hot_updates,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                CASE 
                    WHEN (seq_scan + idx_scan) > 0 THEN 
                        ROUND(100.0 * seq_scan / (seq_scan + idx_scan), 2)
                    ELSE 0 
                END AS seq_scan_ratio,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY {order_clause}
            LIMIT %s
        """, (limit,))
        
        tables = []
        issues = []
        
        for row in cur.fetchall():
            table_issues = []
            
            # Check for issues
            if row['bloat_ratio'] and row['bloat_ratio'] > 20:
                table_issues.append(f"High bloat: {row['bloat_ratio']}%")
            
            if row['seq_scan_ratio'] and row['seq_scan_ratio'] > 75 and row['seq_scan'] > 1000:
                table_issues.append(f"Too many seq scans: {row['seq_scan_ratio']}%")
            
            if row['last_autovacuum'] and row['last_autovacuum'] < datetime.now() - timedelta(days=7):
                table_issues.append("Needs vacuum (>7 days)")
            
            tables.append({
                "schema": row['schemaname'],
                "table": row['tablename'],
                "size": row['size'],
                "size_bytes": row['size_bytes'],
                "rows": {
                    "live": row['live_rows'],
                    "dead": row['dead_rows'],
                    "bloat_ratio": float(row['bloat_ratio'] or 0)
                },
                "activity": {
                    "inserts": row['inserts'],
                    "updates": row['updates'],
                    "deletes": row['deletes'],
                    "hot_updates": row['hot_updates']
                },
                "scans": {
                    "sequential": row['seq_scan'],
                    "index": row['idx_scan'],
                    "seq_ratio": float(row['seq_scan_ratio'] or 0)
                },
                "maintenance": {
                    "last_vacuum": row['last_vacuum'].isoformat() if row['last_vacuum'] else None,
                    "last_autovacuum": row['last_autovacuum'].isoformat() if row['last_autovacuum'] else None,
                    "last_analyze": row['last_analyze'].isoformat() if row['last_analyze'] else None
                },
                "issues": table_issues
            })
            
            if table_issues:
                issues.extend(table_issues)
        
        cur.close()
        conn.close()
        
        return {
            "tables": tables,
            "total_issues": len(issues),
            "ordered_by": order_by,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error analyzing tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# INDEX OPTIMIZATION
# ============================================================================

@router.get("/indexes/missing")
async def find_missing_indexes():
    """Identify tables that need indexes"""
    try:
        conn = get_master_connection()
        cur = conn.cursor()
        
        # Find tables with high sequential scan ratios
        cur.execute("""
            SELECT 
                schemaname,
                tablename,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                n_live_tup,
                CASE 
                    WHEN (seq_scan + COALESCE(idx_scan, 0)) > 0 THEN 
                        ROUND(100.0 * seq_scan / (seq_scan + COALESCE(idx_scan, 0)), 2)
                    ELSE 0 
                END AS seq_scan_ratio
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
                AND seq_scan > 100
                AND seq_tup_read > 10000
                AND n_live_tup > 1000
            ORDER BY seq_tup_read DESC
            LIMIT 20
        """)
        
        recommendations = []
        for row in cur.fetchall():
            if row['seq_scan_ratio'] > 50:  # More than 50% sequential scans
                # Try to identify columns that might benefit from indexes
                cur.execute("""
                    SELECT 
                        a.attname as column_name,
                        t.typname as data_type
                    FROM pg_attribute a
                    JOIN pg_type t ON a.atttypid = t.oid
                    WHERE a.attrelid = %s::regclass
                    AND a.attnum > 0
                    AND NOT a.attisdropped
                    AND a.attname NOT IN (
                        SELECT a.attname
                        FROM pg_index i
                        JOIN pg_attribute a ON a.attrelid = i.indrelid
                        WHERE i.indrelid = %s::regclass
                        AND a.attnum = ANY(i.indkey)
                    )
                    ORDER BY a.attnum
                    LIMIT 5
                """, (f"public.{row['tablename']}", f"public.{row['tablename']}"))
                
                unindexed_columns = [col['column_name'] for col in cur.fetchall()]
                
                recommendations.append({
                    "table": row['tablename'],
                    "seq_scans": row['seq_scan'],
                    "rows_read_sequentially": row['seq_tup_read'],
                    "index_scans": row['idx_scan'] or 0,
                    "seq_scan_ratio": float(row['seq_scan_ratio']),
                    "table_size": row['n_live_tup'],
                    "unindexed_columns": unindexed_columns[:3],  # Top 3 candidates
                    "recommendation": f"CREATE INDEX idx_{row['tablename']}_column ON {row['tablename']} (column_name);"
                })
        
        # Find unused indexes
        cur.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
                AND idx_scan = 0
                AND indexrelname NOT LIKE '%_pkey'
            ORDER BY pg_relation_size(indexrelid) DESC
            LIMIT 10
        """)
        
        unused_indexes = []
        for row in cur.fetchall():
            unused_indexes.append({
                "table": row['tablename'],
                "index": row['indexname'],
                "size": row['index_size'],
                "scans": row['idx_scan'],
                "recommendation": f"DROP INDEX {row['indexname']}; -- Never used"
            })
        
        cur.close()
        conn.close()
        
        return {
            "missing_indexes": recommendations,
            "unused_indexes": unused_indexes,
            "total_recommendations": len(recommendations) + len(unused_indexes)
        }
    except Exception as e:
        logger.error(f"Error finding missing indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# OPTIMIZE DATABASE
# ============================================================================

@router.post("/optimize")
async def optimize_database(
    background_tasks: BackgroundTasks,
    vacuum_tables: bool = True,
    analyze_tables: bool = True,
    reindex: bool = False
):
    """Run database optimization tasks"""
    
    def run_optimization():
        try:
            conn = get_master_connection()
            conn.autocommit = True
            cur = conn.cursor()
            
            results = []
            
            if vacuum_tables:
                # Find tables that need vacuum
                cur.execute("""
                    SELECT tablename 
                    FROM pg_stat_user_tables 
                    WHERE schemaname = 'public' 
                        AND (n_dead_tup > 1000 OR last_autovacuum < NOW() - INTERVAL '7 days')
                    ORDER BY n_dead_tup DESC
                    LIMIT 10
                """)
                
                for row in cur.fetchall():
                    try:
                        cur.execute(f"VACUUM ANALYZE {row['tablename']}")
                        results.append(f"✅ VACUUM ANALYZE {row['tablename']}")
                        logger.info(f"Vacuumed table: {row['tablename']}")
                    except Exception as e:
                        results.append(f"❌ Failed to vacuum {row['tablename']}: {str(e)}")
                        logger.error(f"Failed to vacuum {row['tablename']}: {e}")
            
            if analyze_tables:
                try:
                    cur.execute("ANALYZE")
                    results.append("✅ Updated database statistics")
                    logger.info("Updated database statistics")
                except Exception as e:
                    results.append(f"❌ Failed to analyze: {str(e)}")
                    logger.error(f"Failed to analyze: {e}")
            
            if reindex:
                # Reindex most fragmented indexes
                cur.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname
                    FROM pg_stat_user_indexes
                    WHERE schemaname = 'public'
                    ORDER BY idx_scan DESC
                    LIMIT 5
                """)
                
                for row in cur.fetchall():
                    try:
                        cur.execute(f"REINDEX INDEX {row['indexname']}")
                        results.append(f"✅ REINDEX {row['indexname']}")
                        logger.info(f"Reindexed: {row['indexname']}")
                    except Exception as e:
                        results.append(f"❌ Failed to reindex {row['indexname']}: {str(e)}")
                        logger.error(f"Failed to reindex {row['indexname']}: {e}")
            
            cur.close()
            conn.close()
            
            # Store results
            logger.info(f"Optimization complete: {results}")
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
    
    # Run in background
    background_tasks.add_task(run_optimization)
    
    return {
        "status": "started",
        "tasks": {
            "vacuum": vacuum_tables,
            "analyze": analyze_tables,
            "reindex": reindex
        },
        "message": "Optimization started in background",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def database_health():
    """Comprehensive database health check"""
    try:
        health = {
            "status": "checking",
            "checks": {},
            "score": 100,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        conn = get_master_connection()
        cur = conn.cursor()
        
        # Check connection pool
        cur.execute("""
            SELECT 
                (SELECT count(*) FROM pg_stat_activity) as connections,
                (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_conn
        """)
        conn_data = cur.fetchone()
        conn_usage = (conn_data['connections'] / conn_data['max_conn']) * 100
        
        health['checks']['connections'] = {
            "status": "healthy" if conn_usage < 80 else "warning" if conn_usage < 90 else "critical",
            "usage_percent": round(conn_usage, 2)
        }
        if conn_usage > 80:
            health['score'] -= 10
        
        # Check cache hit ratio
        cur.execute("""
            SELECT 
                sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100 as ratio
            FROM pg_statio_user_tables
        """)
        cache_ratio = float(cur.fetchone()['ratio'] or 0)
        
        health['checks']['cache'] = {
            "status": "healthy" if cache_ratio > 90 else "warning" if cache_ratio > 80 else "critical",
            "hit_ratio": round(cache_ratio, 2)
        }
        if cache_ratio < 90:
            health['score'] -= 15
        
        # Check for bloat
        cur.execute("""
            SELECT COUNT(*) as bloated
            FROM pg_stat_user_tables
            WHERE n_dead_tup > 10000
                AND n_live_tup > 0
                AND (n_dead_tup::float / n_live_tup) > 0.2
        """)
        bloated = cur.fetchone()['bloated']
        
        health['checks']['bloat'] = {
            "status": "healthy" if bloated == 0 else "warning" if bloated < 5 else "critical",
            "bloated_tables": bloated
        }
        if bloated > 0:
            health['score'] -= (5 * min(bloated, 5))
        
        # Check replication lag
        cur.execute("""
            SELECT 
                COUNT(*) as replicas,
                MAX(EXTRACT(EPOCH FROM replay_lag)) as max_lag_seconds
            FROM pg_stat_replication
        """)
        repl_data = cur.fetchone()
        
        if repl_data['replicas'] > 0:
            lag = float(repl_data['max_lag_seconds'] or 0)
            health['checks']['replication'] = {
                "status": "healthy" if lag < 1 else "warning" if lag < 5 else "critical",
                "max_lag_seconds": round(lag, 2),
                "replica_count": repl_data['replicas']
            }
            if lag > 1:
                health['score'] -= 10
        
        cur.close()
        conn.close()
        
        # Overall status
        if health['score'] >= 90:
            health['status'] = "healthy"
        elif health['score'] >= 70:
            health['status'] = "warning"
        else:
            health['status'] = "critical"
        
        return health
        
    except Exception as e:
        logger.error(f"Error checking database health: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ============================================================================
# REALTIME MONITORING
# ============================================================================

@router.get("/monitor/realtime")
async def realtime_monitoring():
    """Get realtime database activity"""
    try:
        conn = get_master_connection()
        cur = conn.cursor()
        
        # Current activity
        cur.execute("""
            SELECT 
                pid,
                usename,
                application_name,
                client_addr,
                state,
                query_start,
                state_change,
                wait_event_type,
                wait_event,
                LEFT(query, 100) as query_preview
            FROM pg_stat_activity
            WHERE state != 'idle'
                AND pid != pg_backend_pid()
            ORDER BY query_start
        """)
        
        active_queries = []
        for row in cur.fetchall():
            active_queries.append({
                "pid": row['pid'],
                "user": row['usename'],
                "application": row['application_name'],
                "client": str(row['client_addr']),
                "state": row['state'],
                "duration": str(datetime.now() - row['query_start']) if row['query_start'] else None,
                "waiting": f"{row['wait_event_type']}: {row['wait_event']}" if row['wait_event_type'] else None,
                "query": row['query_preview']
            })
        
        # Transaction stats
        cur.execute("""
            SELECT 
                datname,
                xact_commit,
                xact_rollback,
                blks_read,
                blks_hit,
                tup_returned,
                tup_fetched,
                tup_inserted,
                tup_updated,
                tup_deleted
            FROM pg_stat_database
            WHERE datname = 'postgres'
        """)
        db_stats = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            "active_queries": active_queries,
            "query_count": len(active_queries),
            "database_stats": {
                "transactions": {
                    "committed": db_stats['xact_commit'],
                    "rolled_back": db_stats['xact_rollback'],
                    "rollback_ratio": round(db_stats['xact_rollback'] / max(db_stats['xact_commit'], 1) * 100, 2)
                },
                "blocks": {
                    "read": db_stats['blks_read'],
                    "hit": db_stats['blks_hit'],
                    "hit_ratio": round(db_stats['blks_hit'] / max(db_stats['blks_hit'] + db_stats['blks_read'], 1) * 100, 2)
                },
                "tuples": {
                    "returned": db_stats['tup_returned'],
                    "fetched": db_stats['tup_fetched'],
                    "inserted": db_stats['tup_inserted'],
                    "updated": db_stats['tup_updated'],
                    "deleted": db_stats['tup_deleted']
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting realtime monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))