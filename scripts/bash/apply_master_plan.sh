#!/bin/bash
# BrainOps AI OS - Master Plan Application Script
# Version: 1.0.0
# Created: 2025-01-17
# Applies all database migrations and seeds for the Master To-Do Plan

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${SCRIPT_DIR}/master_plan_${TIMESTAMP}.log"

# Database connection (from environment or defaults)
DB_HOST="${DATABASE_HOST:-db.yomagoqdmxszqtdwuhab.supabase.co}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-postgres}"
DB_USER="${DATABASE_USER:-postgres}"
DB_PASS="${DATABASE_PASSWORD:-Brain0ps2O2S}"
DATABASE_URL="${DATABASE_URL:-postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}}"

# Function to log messages
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        ERROR)
            echo -e "${RED}[ERROR]${NC} ${message}" | tee -a "$LOG_FILE"
            ;;
        SUCCESS)
            echo -e "${GREEN}[SUCCESS]${NC} ${message}" | tee -a "$LOG_FILE"
            ;;
        WARNING)
            echo -e "${YELLOW}[WARNING]${NC} ${message}" | tee -a "$LOG_FILE"
            ;;
        INFO)
            echo -e "${BLUE}[INFO]${NC} ${message}" | tee -a "$LOG_FILE"
            ;;
        *)
            echo "[${timestamp}] ${message}" | tee -a "$LOG_FILE"
            ;;
    esac
}

# Function to execute SQL file
execute_sql() {
    local sql_file=$1
    local description=$2
    
    log INFO "Executing: ${description}"
    
    if [ ! -f "$sql_file" ]; then
        log ERROR "SQL file not found: $sql_file"
        return 1
    fi
    
    # Execute with timing and error handling
    if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -v ON_ERROR_STOP=1 \
        -f "$sql_file" \
        >> "$LOG_FILE" 2>&1; then
        log SUCCESS "${description} completed"
        return 0
    else
        log ERROR "${description} failed - check $LOG_FILE for details"
        return 1
    fi
}

# Function to verify connection
verify_connection() {
    log INFO "Verifying database connection..."
    
    if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "SELECT version();" > /dev/null 2>&1; then
        log SUCCESS "Database connection verified"
        return 0
    else
        log ERROR "Cannot connect to database"
        return 1
    fi
}

# Function to create backup
create_backup() {
    log INFO "Creating database backup..."
    
    local backup_file="${SCRIPT_DIR}/backup_${TIMESTAMP}.sql"
    
    if PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --schema=task_os --schema=core --schema=ops --schema=memory --schema=docs --schema=data --schema=email --schema=revenue \
        --if-exists --clean \
        > "$backup_file" 2>> "$LOG_FILE"; then
        log SUCCESS "Backup created: $backup_file"
        return 0
    else
        log WARNING "Backup creation failed - proceeding anyway"
        return 0
    fi
}

# Function to verify schema creation
verify_schema() {
    log INFO "Verifying schema creation..."
    
    local schema_check=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -t -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name IN ('task_os', 'core', 'ops', 'memory', 'docs', 'data', 'email', 'revenue');" 2>/dev/null)
    
    schema_check=$(echo $schema_check | tr -d ' ')
    
    if [ "$schema_check" -eq "8" ]; then
        log SUCCESS "All schemas created successfully"
        return 0
    else
        log ERROR "Expected 8 schemas, found $schema_check"
        return 1
    fi
}

# Function to get task statistics
get_task_stats() {
    log INFO "Retrieving task statistics..."
    
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "SELECT * FROM task_os.task_status_summary;" \
        2>> "$LOG_FILE" | tee -a "$LOG_FILE"
    
    local epic_count=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -t -c "SELECT COUNT(*) FROM task_os.epics;" 2>/dev/null)
    local story_count=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -t -c "SELECT COUNT(*) FROM task_os.stories;" 2>/dev/null)
    local task_count=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -t -c "SELECT COUNT(*) FROM task_os.tasks;" 2>/dev/null)
    
    log SUCCESS "Loaded: ${epic_count} epics, ${story_count} stories, ${task_count} tasks"
}

# Function to generate IDs for persistence
generate_ids() {
    log INFO "Generating persistence IDs..."
    
    local result=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -t -c "SELECT id, title FROM task_os.epics ORDER BY created_at LIMIT 5;" 2>/dev/null)
    
    echo "$result" | while IFS='|' read -r id title; do
        id=$(echo $id | tr -d ' ')
        title=$(echo $title | xargs)
        if [ ! -z "$id" ]; then
            log INFO "Epic ID: $id - $title"
        fi
    done
}

# Main execution
main() {
    echo "=========================================="
    echo "BrainOps AI OS - Master Plan Deployment"
    echo "=========================================="
    echo "Timestamp: $(date)"
    echo "Log file: $LOG_FILE"
    echo ""
    
    # Step 1: Verify connection
    if ! verify_connection; then
        log ERROR "Cannot proceed without database connection"
        exit 1
    fi
    
    # Step 2: Create backup (optional, non-blocking)
    create_backup
    
    # Step 3: Apply migrations in order
    log INFO "Starting migration sequence..."
    
    # Apply schema migrations
    if ! execute_sql "${SCRIPT_DIR}/001_master_todo_plan_schema.sql" "Master To-Do Plan Schema"; then
        log ERROR "Schema creation failed"
        exit 1
    fi
    
    if ! execute_sql "${SCRIPT_DIR}/003_persistent_memory_schema.sql" "Persistent Memory Schema"; then
        log ERROR "Memory schema creation failed"
        exit 1
    fi
    
    # Apply seed data
    if ! execute_sql "${SCRIPT_DIR}/002_master_todo_plan_seed.sql" "Master To-Do Plan Seed Data"; then
        log ERROR "Seed data loading failed"
        exit 1
    fi
    
    # Step 4: Verify deployment
    if ! verify_schema; then
        log WARNING "Schema verification failed - manual review required"
    fi
    
    # Step 5: Display statistics
    get_task_stats
    
    # Step 6: Generate persistence IDs
    generate_ids
    
    # Step 7: Create marker file for idempotency
    echo "$(date): Master Plan v1.0.0 deployed" > "${SCRIPT_DIR}/.master_plan_deployed"
    
    echo ""
    echo "=========================================="
    log SUCCESS "Master Plan deployment completed successfully!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Review the task hierarchy in the database"
    echo "2. Start the Task OS service"
    echo "3. Configure Slack integration"
    echo "4. Begin processing tasks from the queue"
    echo ""
    echo "To query tasks:"
    echo "  psql \$DATABASE_URL -c \"SELECT * FROM task_os.get_task_hierarchy();\""
    echo ""
    echo "Log file: $LOG_FILE"
}

# Trap errors
trap 'log ERROR "Script failed at line $LINENO"' ERR

# Run main function
main "$@"