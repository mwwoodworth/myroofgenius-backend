#!/bin/bash

# AI DevOps System Startup Script
# This script initializes and starts the complete AI DevOps system

set -e  # Exit on any error

echo "🚀 Starting AI DevOps System..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Check if we're in the right directory
if [[ ! -f "ai_devops_orchestrator.py" ]]; then
    print_error "Please run this script from the ai_devops_system directory"
    exit 1
fi

# Activate virtual environment
print_section "Activating Virtual Environment"
if [[ -f "../ai_devops_env/bin/activate" ]]; then
    source ../ai_devops_env/bin/activate
    print_status "Virtual environment activated"
else
    print_warning "Virtual environment not found, using system Python"
fi

# Check required services
print_section "Checking Required Services"

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    print_status "Redis is running"
else
    print_warning "Redis is not running, attempting to start..."
    sudo systemctl start redis-server || print_error "Failed to start Redis"
fi

# Check PostgreSQL
if systemctl is-active --quiet postgresql; then
    print_status "PostgreSQL is running"
else
    print_warning "PostgreSQL is not running, attempting to start..."
    sudo systemctl start postgresql || print_error "Failed to start PostgreSQL"
fi

# Check Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_status "Ollama is running"
else
    print_warning "Ollama is not running, attempting to start..."
    sudo systemctl start ollama || print_error "Failed to start Ollama"
fi

# Check Docker
if docker ps > /dev/null 2>&1; then
    print_status "Docker is running"
else
    print_warning "Docker is not running, attempting to start..."
    sudo systemctl start docker || print_error "Failed to start Docker"
fi

# Check AnythingLLM container
if docker ps | grep -q anythingllm-container; then
    print_status "AnythingLLM container is running"
else
    print_warning "AnythingLLM container not running, attempting to start..."
    if docker ps -a | grep -q anythingllm-container; then
        docker start anythingllm-container || print_error "Failed to start AnythingLLM container"
    else
        print_warning "AnythingLLM container not found, it may still be downloading"
    fi
fi

# Create necessary directories
print_section "Setting up Directories"
mkdir -p logs
mkdir -p data
mkdir -p chroma_db
mkdir -p ~/.anythingllm
print_status "Directories created"

# Setup PostgreSQL database (if needed)
print_section "Setting up Database"
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw ai_memory; then
    print_status "ai_memory database exists"
else
    print_warning "Creating ai_memory database..."
    sudo -u postgres createdb ai_memory || print_warning "Database creation failed or already exists"
fi

# Enable pgvector extension
sudo -u postgres psql -d ai_memory -c "CREATE EXTENSION IF NOT EXISTS vector;" > /dev/null 2>&1
print_status "pgvector extension enabled"

# Install any missing Python dependencies
print_section "Checking Python Dependencies"
if python -c "import fastapi, uvicorn, redis, psycopg2, chromadb, sentence_transformers, docker, psutil, prometheus_client" 2>/dev/null; then
    print_status "All Python dependencies are available"
else
    print_warning "Some Python dependencies may be missing"
    # Attempt to install
    pip install fastapi uvicorn redis psycopg2-binary chromadb sentence-transformers docker psutil prometheus_client schedule
fi

# Start the system
print_section "Starting AI DevOps System"

# Function to handle graceful shutdown
cleanup() {
    print_warning "Shutting down AI DevOps System..."
    if [[ ! -z "$ORCHESTRATOR_PID" ]]; then
        kill $ORCHESTRATOR_PID
    fi
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Check for command line arguments
MODE=${1:-server}
HOST=${2:-0.0.0.0}
PORT=${3:-8080}

print_status "Starting AI DevOps Orchestrator in $MODE mode..."

# Run based on mode
case $MODE in
    "server")
        print_status "Starting server on $HOST:$PORT"
        print_status "API will be available at: http://$HOST:$PORT"
        print_status "Health check: http://$HOST:$PORT/health"
        print_status "System info: http://$HOST:$PORT/system/info"
        print_status "Metrics: http://$HOST:8000/metrics (Prometheus)"
        print_status "AnythingLLM: http://localhost:3001"
        print_status ""
        print_status "Press Ctrl+C to stop the system"
        
        python ai_devops_orchestrator.py --host $HOST --port $PORT &
        ORCHESTRATOR_PID=$!
        
        # Wait for the process
        wait $ORCHESTRATOR_PID
        ;;
    "status")
        print_status "Checking system status..."
        python ai_devops_orchestrator.py --mode status
        ;;
    "test")
        print_status "Running system tests..."
        python ai_devops_orchestrator.py --mode test
        ;;
    *)
        print_error "Invalid mode: $MODE"
        echo "Usage: $0 [server|status|test] [host] [port]"
        exit 1
        ;;
esac