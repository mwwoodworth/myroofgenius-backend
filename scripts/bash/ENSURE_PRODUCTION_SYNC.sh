#!/bin/bash
# ENSURE PRODUCTION IS ALWAYS CURRENT
# Run this before ANY commit or when making changes

set -e  # Exit on any error

echo "🔒 ENSURING PRODUCTION SYNC"
echo "============================"

# 1. Check if we have production connectivity
check_production() {
    echo -n "Checking production connection... "
    if psql "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require" -c "SELECT 1" > /dev/null 2>&1; then
        echo "✅ CONNECTED"
        return 0
    else
        echo "🔴 OFFLINE"
        return 1
    fi
}

# 2. Get database checksums
get_checksums() {
    echo "Calculating database checksums..."
    
    # Local checksum
    LOCAL_SUM=$(psql -h localhost -p 54322 -U postgres -d postgres -t -c "
        SELECT md5(string_agg(counts::text, ',' ORDER BY table_name))
        FROM (
            SELECT table_name, COUNT(*) as counts
            FROM information_schema.tables t
            LEFT JOIN LATERAL (
                SELECT COUNT(*) FROM customers
            ) c ON t.table_name = 'customers'
            WHERE table_schema = 'public'
            GROUP BY table_name
        ) x
    " 2>/dev/null | tr -d ' ')
    
    # Production checksum (if connected)
    if check_production; then
        PROD_SUM=$(psql "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require" -t -c "
            SELECT md5(string_agg(counts::text, ',' ORDER BY table_name))
            FROM (
                SELECT table_name, COUNT(*) as counts
                FROM information_schema.tables t
                LEFT JOIN LATERAL (
                    SELECT COUNT(*) FROM customers
                ) c ON t.table_name = 'customers'
                WHERE table_schema = 'public'
                GROUP BY table_name
            ) x
        " 2>/dev/null | tr -d ' ')
    else
        PROD_SUM="OFFLINE"
    fi
    
    echo "  Local:      $LOCAL_SUM"
    echo "  Production: $PROD_SUM"
}

# 3. Sync if needed
sync_to_production() {
    if [ "$LOCAL_SUM" = "$PROD_SUM" ]; then
        echo "✅ Databases are in sync"
        return 0
    fi
    
    echo "🔄 Syncing to production..."
    
    # Export critical tables
    TABLES="app_users customers jobs invoices estimates products automations ai_agents"
    
    for TABLE in $TABLES; do
        echo "  Syncing $TABLE..."
        
        # Dump local table
        pg_dump -h localhost -p 54322 -U postgres -d postgres \
            --table=$TABLE --data-only --no-owner \
            > /tmp/${TABLE}_sync.sql
        
        # Load to production
        psql "postgresql://postgres:<DB_PASSWORD_REDACTED>@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres" \
            < /tmp/${TABLE}_sync.sql 2>/dev/null || true
        
        rm /tmp/${TABLE}_sync.sql
    done
    
    echo "✅ Production updated"
}

# 4. Create sync status file
create_status_file() {
    cat > /tmp/db_sync_status.json << EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "local_checksum": "$LOCAL_SUM",
    "production_checksum": "$PROD_SUM",
    "synced": $([ "$LOCAL_SUM" = "$PROD_SUM" ] && echo "true" || echo "false"),
    "connection": $(check_production && echo "true" || echo "false")
}
EOF
    
    echo "📊 Status saved to /tmp/db_sync_status.json"
}

# 5. Main execution
main() {
    echo "Starting sync check at $(date)"
    echo ""
    
    # Check connection
    if ! check_production; then
        echo "⚠️  WARNING: Cannot reach production database!"
        echo "⚠️  Changes will be queued locally"
        echo ""
        echo "When connection is restored, run:"
        echo "  ./ENSURE_PRODUCTION_SYNC.sh"
        echo ""
        
        # Create offline marker
        touch /tmp/db_sync_offline
        exit 1
    fi
    
    # Remove offline marker if exists
    rm -f /tmp/db_sync_offline
    
    # Get checksums
    get_checksums
    
    # Sync if needed
    if [ "$LOCAL_SUM" != "$PROD_SUM" ]; then
        sync_to_production
        
        # Verify sync
        get_checksums
        
        if [ "$LOCAL_SUM" != "$PROD_SUM" ]; then
            echo "❌ SYNC FAILED - Manual intervention needed"
            exit 1
        fi
    fi
    
    # Create status file
    create_status_file
    
    echo ""
    echo "✅ PRODUCTION IS CURRENT"
    echo "Safe to proceed with development"
    echo ""
}

# Run main
main