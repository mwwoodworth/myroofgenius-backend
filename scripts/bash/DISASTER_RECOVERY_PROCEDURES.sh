#!/bin/bash
# BrainOps Disaster Recovery Procedures
# Version: 1.0.0
# Last Updated: 2025-08-18

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKUP_DIR="/home/mwwoodworth/backups"
DB_BACKUP_DIR="$BACKUP_DIR/database"
CODE_BACKUP_DIR="$BACKUP_DIR/code"
CONFIG_BACKUP_DIR="$BACKUP_DIR/config"
RECOVERY_LOG="/tmp/disaster_recovery_$(date +%Y%m%d_%H%M%S).log"

# Database credentials
DB_HOST="aws-0-us-east-2.pooler.supabase.com"
DB_PORT="6543"
DB_NAME="postgres"
DB_USER="postgres.yomagoqdmxszqtdwuhab"
export PGPASSWORD="Brain0ps2O2S"

# Initialize
mkdir -p "$DB_BACKUP_DIR" "$CODE_BACKUP_DIR" "$CONFIG_BACKUP_DIR"

log() {
    echo -e "$1" | tee -a "$RECOVERY_LOG"
}

# Function: System Health Check
health_check() {
    log "${BLUE}🔍 SYSTEM HEALTH CHECK${NC}"
    log "========================"
    
    # Check API
    API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://brainops-backend-prod.onrender.com/api/v1/health)
    if [ "$API_STATUS" = "200" ]; then
        log "${GREEN}✅ API: Operational${NC}"
    else
        log "${RED}❌ API: Down (Status: $API_STATUS)${NC}"
    fi
    
    # Check Database
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
        log "${GREEN}✅ Database: Accessible${NC}"
    else
        log "${RED}❌ Database: Inaccessible${NC}"
    fi
    
    # Check Docker
    if docker ps > /dev/null 2>&1; then
        CONTAINERS=$(docker ps -q | wc -l)
        log "${GREEN}✅ Docker: Running ($CONTAINERS containers)${NC}"
    else
        log "${RED}❌ Docker: Not accessible${NC}"
    fi
    
    # Check critical processes
    PROCESSES=("PERSISTENT_MONITORING_SYSTEM.py" "LOG_AGGREGATOR.py" "METRICS_DASHBOARD.py")
    for PROC in "${PROCESSES[@]}"; do
        if pgrep -f "$PROC" > /dev/null; then
            log "${GREEN}✅ Process $PROC: Running${NC}"
        else
            log "${YELLOW}⚠️ Process $PROC: Not running${NC}"
        fi
    done
}

# Function: Backup Database
backup_database() {
    log "\n${BLUE}💾 BACKING UP DATABASE${NC}"
    log "======================"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$DB_BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    
    # Create full database backup
    log "Creating database backup..."
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$BACKUP_FILE" 2>> "$RECOVERY_LOG"
    
    if [ -f "$BACKUP_FILE" ]; then
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        log "${GREEN}✅ Database backed up: $BACKUP_FILE ($SIZE)${NC}"
        
        # Compress backup
        gzip "$BACKUP_FILE"
        log "${GREEN}✅ Backup compressed: ${BACKUP_FILE}.gz${NC}"
    else
        log "${RED}❌ Database backup failed${NC}"
        return 1
    fi
}

# Function: Backup Code
backup_code() {
    log "\n${BLUE}📦 BACKING UP CODE${NC}"
    log "=================="
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    # Backup critical repositories
    REPOS=("fastapi-operator-env" "myroofgenius-app" "weathercraft-erp")
    
    for REPO in "${REPOS[@]}"; do
        if [ -d "/home/mwwoodworth/code/$REPO" ]; then
            log "Backing up $REPO..."
            tar -czf "$CODE_BACKUP_DIR/${REPO}_$TIMESTAMP.tar.gz" \
                -C "/home/mwwoodworth/code" "$REPO" 2>> "$RECOVERY_LOG"
            log "${GREEN}✅ $REPO backed up${NC}"
        fi
    done
}

# Function: Backup Configurations
backup_configs() {
    log "\n${BLUE}⚙️ BACKING UP CONFIGURATIONS${NC}"
    log "============================"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    # Backup important configs
    CONFIGS=(
        "/home/mwwoodworth/.docker/config.json"
        "/home/mwwoodworth/.config/mcp/config.json"
        "/home/mwwoodworth/code/docker-compose.monitoring.yml"
        "/home/mwwoodworth/code/prometheus.yml"
    )
    
    for CONFIG in "${CONFIGS[@]}"; do
        if [ -f "$CONFIG" ]; then
            BASENAME=$(basename "$CONFIG")
            cp "$CONFIG" "$CONFIG_BACKUP_DIR/${BASENAME}_$TIMESTAMP" 2>> "$RECOVERY_LOG"
            log "${GREEN}✅ Backed up: $BASENAME${NC}"
        fi
    done
    
    # Backup environment variables
    env > "$CONFIG_BACKUP_DIR/environment_$TIMESTAMP.env"
    
    # Backup crontab
    crontab -l > "$CONFIG_BACKUP_DIR/crontab_$TIMESTAMP.txt" 2>> "$RECOVERY_LOG"
    
    log "${GREEN}✅ Configuration backup complete${NC}"
}

# Function: Restore Database
restore_database() {
    log "\n${BLUE}🔄 RESTORING DATABASE${NC}"
    log "====================="
    
    # Find latest backup
    LATEST_BACKUP=$(ls -t "$DB_BACKUP_DIR"/*.sql.gz 2>/dev/null | head -1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        log "${RED}❌ No database backup found${NC}"
        return 1
    fi
    
    log "Found backup: $LATEST_BACKUP"
    log "${YELLOW}⚠️ WARNING: This will overwrite the current database!${NC}"
    read -p "Continue? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Decompress backup
        gunzip -c "$LATEST_BACKUP" > /tmp/restore.sql
        
        # Restore database
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < /tmp/restore.sql 2>> "$RECOVERY_LOG"
        
        rm /tmp/restore.sql
        log "${GREEN}✅ Database restored from backup${NC}"
    else
        log "Database restore cancelled"
    fi
}

# Function: Emergency Recovery
emergency_recovery() {
    log "\n${RED}🚨 EMERGENCY RECOVERY MODE${NC}"
    log "=========================="
    
    # 1. Stop all services
    log "\n${YELLOW}Stopping all services...${NC}"
    pkill -f "PERSISTENT_MONITORING_SYSTEM.py" || true
    pkill -f "LOG_AGGREGATOR.py" || true
    pkill -f "METRICS_DASHBOARD.py" || true
    pkill -f "CENTERPOINT_24_7_SYNC_SERVICE.py" || true
    docker-compose -f /home/mwwoodworth/code/docker-compose.monitoring.yml down || true
    
    # 2. Clear temporary files
    log "\n${YELLOW}Clearing temporary files...${NC}"
    rm -f /tmp/*.log
    
    # 3. Restart Docker
    log "\n${YELLOW}Restarting Docker...${NC}"
    sudo systemctl restart docker || true
    
    # 4. Restart critical services
    log "\n${YELLOW}Starting critical services...${NC}"
    
    # Start monitoring
    nohup python3 /home/mwwoodworth/code/PERSISTENT_MONITORING_SYSTEM.py > /tmp/persistent_monitor.log 2>&1 &
    nohup python3 /home/mwwoodworth/code/LOG_AGGREGATOR.py > /tmp/log_aggregator.log 2>&1 &
    nohup python3 /home/mwwoodworth/code/METRICS_DASHBOARD.py > /tmp/metrics_dashboard.log 2>&1 &
    
    # Start Docker monitoring
    docker-compose -f /home/mwwoodworth/code/docker-compose.monitoring.yml up -d
    
    # 5. Test connectivity
    sleep 5
    health_check
    
    log "\n${GREEN}✅ Emergency recovery complete${NC}"
}

# Function: Create Recovery Snapshot
create_snapshot() {
    log "\n${BLUE}📸 CREATING RECOVERY SNAPSHOT${NC}"
    log "============================="
    
    SNAPSHOT_NAME="snapshot_$(date +%Y%m%d_%H%M%S)"
    SNAPSHOT_DIR="$BACKUP_DIR/$SNAPSHOT_NAME"
    
    mkdir -p "$SNAPSHOT_DIR"
    
    # Full system backup
    backup_database
    backup_code
    backup_configs
    
    # Create snapshot manifest
    cat > "$SNAPSHOT_DIR/manifest.json" << MANIFEST
{
    "timestamp": "$(date -Iseconds)",
    "type": "full_snapshot",
    "components": {
        "database": true,
        "code": true,
        "configs": true
    },
    "system_state": {
        "api_status": "$API_STATUS",
        "docker_containers": $(docker ps -q | wc -l),
        "database_size": "$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'))" 2>/dev/null | tr -d ' ')"
    }
}
MANIFEST
    
    log "${GREEN}✅ Snapshot created: $SNAPSHOT_NAME${NC}"
}

# Main menu
show_menu() {
    clear
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  DISASTER RECOVERY SYSTEM${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
    echo "1) System Health Check"
    echo "2) Create Full Backup"
    echo "3) Backup Database Only"
    echo "4) Backup Code Only"
    echo "5) Backup Configurations"
    echo "6) Restore Database"
    echo "7) Emergency Recovery"
    echo "8) Create Recovery Snapshot"
    echo "9) View Recovery Log"
    echo "0) Exit"
    echo
    read -p "Select option: " choice
    
    case $choice in
        1) health_check ;;
        2) backup_database; backup_code; backup_configs ;;
        3) backup_database ;;
        4) backup_code ;;
        5) backup_configs ;;
        6) restore_database ;;
        7) emergency_recovery ;;
        8) create_snapshot ;;
        9) less "$RECOVERY_LOG" ;;
        0) exit 0 ;;
        *) log "${RED}Invalid option${NC}" ;;
    esac
    
    echo
    read -p "Press Enter to continue..."
    show_menu
}

# Command line arguments
if [ "$1" = "--auto" ]; then
    # Automated backup mode
    log "${BLUE}Running automated backup...${NC}"
    backup_database
    backup_code
    backup_configs
    log "${GREEN}✅ Automated backup complete${NC}"
elif [ "$1" = "--health" ]; then
    health_check
elif [ "$1" = "--emergency" ]; then
    emergency_recovery
else
    show_menu
fi
