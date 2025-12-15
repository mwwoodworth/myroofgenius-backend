#!/bin/bash

# BrainOps Ultimate DevOps Launcher
# One-click setup for complete production mirror environment

set -e

echo "=============================================================="
echo "  🚀 BRAINOPS ULTIMATE DEVOPS LAUNCHER"
echo "=============================================================="
echo "Time: $(date)"
echo "User: $USER"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running with required permissions
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}This script needs sudo access. Please enter your password:${NC}"
    sudo -v
fi

# Function to check command existence
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${YELLOW}$1 not found. Installing...${NC}"
        sudo apt-get install -y $2 || sudo snap install $2
    else
        echo -e "${GREEN}✓ $1 installed${NC}"
    fi
}

# Step 1: Install Prerequisites
echo -e "\n${GREEN}Step 1: Installing Prerequisites...${NC}"
sudo apt-get update -qq

check_command docker docker.io
check_command docker-compose docker-compose
check_command node nodejs
check_command npm npm
check_command psql postgresql-client
check_command redis-cli redis-tools
check_command chromium chromium-browser
check_command vercel vercel

# Install Python packages
echo -e "${GREEN}Installing Python packages...${NC}"
pip3 install -q docker psycopg2-binary redis selenium pytest requests pyyaml python-dotenv notion-client

# Step 2: Set up Docker Environment
echo -e "\n${GREEN}Step 2: Setting up Docker Environment...${NC}"

# Ensure Docker service is running
sudo systemctl start docker
sudo usermod -aG docker $USER

# Create Docker network
docker network create brainops-network 2>/dev/null || true

# Step 3: Clone Repositories
echo -e "\n${GREEN}Step 3: Setting up Repositories...${NC}"

REPOS_DIR="$HOME/code"
mkdir -p $REPOS_DIR

# Clone repositories if they don't exist
repos=(
    "myroofgenius-app:https://github.com/mwwoodworth/myroofgenius-app.git"
    "weathercraft-erp:https://github.com/mwwoodworth/weathercraft-erp.git"
    "brainops-task-os:https://github.com/mwwoodworth/brainops-task-os.git"
)

for repo_info in "${repos[@]}"; do
    IFS=':' read -r repo_name repo_url <<< "$repo_info"
    if [ ! -d "$REPOS_DIR/$repo_name" ]; then
        echo "  Cloning $repo_name..."
        git clone $repo_url "$REPOS_DIR/$repo_name"
    else
        echo "  ✓ $repo_name already exists"
    fi

    # Install npm dependencies
    if [ -f "$REPOS_DIR/$repo_name/package.json" ]; then
        echo "  Installing dependencies for $repo_name..."
        (cd "$REPOS_DIR/$repo_name" && npm install --silent)
    fi
done

# Step 4: Create Environment Files
echo -e "\n${GREEN}Step 4: Creating Environment Configuration...${NC}"

# Create .env file for Docker Compose
cat > .env <<EOF
# Database
DATABASE_URL=postgresql://postgres:<DB_PASSWORD_REDACTED>@localhost:5432/postgres
PROD_DATABASE_URL=postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://yomagoqdmxszqtdwuhab.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<JWT_REDACTED>

# Redis
REDIS_URL=redis://localhost:6379

# Notion
NOTION_TOKEN=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

# AI Keys (add your own)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
EOF

echo "  ✓ Environment configuration created"

# Step 5: Launch Docker Services
echo -e "\n${GREEN}Step 5: Launching Docker Services...${NC}"

# Check if docker-compose.ultimate.yml exists
if [ ! -f "docker-compose.ultimate.yml" ]; then
    echo "  Creating docker-compose.ultimate.yml..."
    # Use the existing docker-compose.devops.yml as base
    cp docker-compose.devops.yml docker-compose.ultimate.yml 2>/dev/null || true
fi

# Start services
echo "  Starting Docker containers..."
docker-compose -f docker-compose.ultimate.yml up -d

# Wait for services to be ready
echo "  Waiting for services to initialize..."
sleep 10

# Step 6: Start Frontend Applications
echo -e "\n${GREEN}Step 6: Starting Frontend Applications...${NC}"

# Start MyRoofGenius
if [ -d "$REPOS_DIR/myroofgenius-app" ]; then
    echo "  Starting MyRoofGenius on port 3000..."
    (cd "$REPOS_DIR/myroofgenius-app" && npm run dev -- -p 3000 > /dev/null 2>&1 &)
    echo "  ✓ MyRoofGenius: http://localhost:3000"
fi

# Start WeatherCraft
if [ -d "$REPOS_DIR/weathercraft-erp" ]; then
    echo "  Starting WeatherCraft on port 3001..."
    (cd "$REPOS_DIR/weathercraft-erp" && npm run dev -- -p 3001 > /dev/null 2>&1 &)
    echo "  ✓ WeatherCraft: http://localhost:3001"
fi

# Step 7: Health Checks
echo -e "\n${GREEN}Step 7: Running Health Checks...${NC}"

services=(
    "Backend API:http://localhost:8000/health"
    "PostgreSQL:localhost:5432"
    "Redis:localhost:6379"
    "Grafana:http://localhost:3002"
    "Portainer:http://localhost:9000"
)

for service_info in "${services[@]}"; do
    IFS=':' read -r service_name service_url <<< "$service_info"

    if [[ $service_url == http* ]]; then
        if curl -s -o /dev/null -w "%{http_code}" $service_url | grep -q "200\|302"; then
            echo -e "  ${GREEN}✓${NC} $service_name: Running"
        else
            echo -e "  ${YELLOW}⚠${NC} $service_name: Starting..."
        fi
    else
        # For non-HTTP services, just check if port is open
        if nc -zv localhost $(echo $service_url | cut -d: -f2) 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} $service_name: Running"
        else
            echo -e "  ${YELLOW}⚠${NC} $service_name: Starting..."
        fi
    fi
done

# Step 8: Create Desktop Shortcuts
echo -e "\n${GREEN}Step 8: Creating Desktop Shortcuts...${NC}"

DESKTOP="$HOME/Desktop"
mkdir -p "$DESKTOP"

# Create launcher for DevOps Dashboard
cat > "$DESKTOP/BrainOps-DevOps.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=BrainOps DevOps Dashboard
Comment=Launch BrainOps Development Environment
Exec=gnome-terminal -- bash -c "cd $(pwd) && python3 ultimate_devops_environment.py; bash"
Icon=utilities-terminal
Terminal=false
Categories=Development;
EOF

chmod +x "$DESKTOP/BrainOps-DevOps.desktop"

# Step 9: Open Browser with All Services
echo -e "\n${GREEN}Step 9: Opening Services in Browser...${NC}"

# Open all services in browser tabs
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8000/docs" &
    sleep 1
    xdg-open "http://localhost:3000" &
    sleep 1
    xdg-open "http://localhost:3001" &
    sleep 1
    xdg-open "http://localhost:3002" &
    sleep 1
    xdg-open "http://localhost:9000" &
fi

# Final Summary
echo -e "\n=============================================================="
echo -e "${GREEN}  ✅ DEVOPS ENVIRONMENT SUCCESSFULLY LAUNCHED!${NC}"
echo -e "=============================================================="
echo -e "\n📊 ${GREEN}Access Points:${NC}"
echo "  • Backend API:    http://localhost:8000"
echo "  • API Docs:       http://localhost:8000/docs"
echo "  • MyRoofGenius:   http://localhost:3000"
echo "  • WeatherCraft:   http://localhost:3001"
echo "  • Grafana:        http://localhost:3002 (admin/BrainOps2025)"
echo "  • Portainer:      http://localhost:9000"
echo "  • Selenium Grid:  http://localhost:4444"
echo ""
echo -e "📝 ${GREEN}Commands:${NC}"
echo "  • Monitor: python3 system_monitor.py"
echo "  • Tests:   python3 chromium_tests.py"
echo "  • Sync:    python3 supabase_sync.py"
echo "  • Logs:    docker-compose -f docker-compose.ultimate.yml logs -f"
echo ""
echo -e "🛑 ${GREEN}To Stop:${NC}"
echo "  docker-compose -f docker-compose.ultimate.yml down"
echo ""
echo "=============================================================="

# Keep script running to show logs
echo -e "\n${YELLOW}Press Ctrl+C to exit (services will continue running)${NC}\n"

# Tail logs
docker-compose -f docker-compose.ultimate.yml logs -f --tail=50