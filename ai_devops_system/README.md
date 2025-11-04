# Ultimate AI DevOps System

A comprehensive AI-powered DevOps automation system that provides intelligent monitoring, persistent memory, auto-healing capabilities, and seamless integration with modern AI tools.

## 🚀 Features

### Core Components
- **Persistent Memory System**: Vector-based memory with ChromaDB and pgvector
- **Intelligent Monitoring**: Real-time system monitoring with auto-healing
- **AI Model Integration**: Ollama, OpenAI, Anthropic support
- **Voice Control**: Whisper-based voice commands
- **Container Management**: Docker integration with AnythingLLM
- **Database Support**: PostgreSQL with pgvector, Redis caching

### AI Capabilities
- **Vector Search**: Semantic search across all stored memories
- **Conversation Memory**: Persistent chat history with context awareness
- **Knowledge Graphs**: Entity relationship tracking
- **Auto-Summarization**: Intelligent conversation summarization
- **Importance Scoring**: Dynamic memory importance calculation

### DevOps Features
- **Auto-Healing**: Automatic service recovery and restart
- **Health Monitoring**: Comprehensive system health checks
- **Alert Management**: Email and webhook notifications
- **Metrics Collection**: Prometheus-compatible metrics
- **Service Discovery**: Automatic service status detection
- **Resource Monitoring**: CPU, memory, disk usage tracking

## 📋 Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Python 3.9+
- Docker
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (for additional tooling)

## 🔧 Installation

### Automated Installation

The system has been pre-installed with all components. To start:

```bash
cd /home/matt-woodworth/fastapi-operator-env/ai_devops_system
./start_ai_devops.sh
```

### Manual Installation

If you need to install from scratch:

```bash
# 1. Install system dependencies
sudo apt update && sudo apt install -y \
    python3 python3-pip python3-venv \
    postgresql postgresql-contrib \
    redis-server docker.io \
    build-essential git curl wget

# 2. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 3. Install pgvector
git clone https://github.com/pgvector/pgvector.git
cd pgvector && make && sudo make install

# 4. Create Python virtual environment
python3 -m venv ai_devops_env
source ai_devops_env/bin/activate

# 5. Install Python packages
pip install -r requirements.txt

# 6. Setup services
sudo systemctl start postgresql redis-server ollama docker
sudo systemctl enable postgresql redis-server ollama docker

# 7. Pull AI models
ollama pull llama3.2:latest
ollama pull codellama:latest

# 8. Start AnythingLLM container
docker run -d -p 3001:3001 --name anythingllm-container mintplexlabs/anythingllm
```

## 🎯 Usage

### Starting the System

```bash
# Start complete system (default mode)
./start_ai_devops.sh

# Start on specific host/port
./start_ai_devops.sh server 0.0.0.0 8080

# Check system status
./start_ai_devops.sh status

# Run system tests
./start_ai_devops.sh test
```

### API Endpoints

The system exposes a comprehensive REST API:

#### Core Endpoints
- `GET /` - System information
- `GET /health` - Health check
- `GET /system/info` - Detailed system info

#### Memory System
- `POST /memory/store` - Store new memory
- `POST /memory/query` - Query memories
- `POST /memory/conversation` - Add conversation
- `GET /memory/context` - Get conversation context
- `GET /memory/stats` - Memory statistics

#### Monitoring
- `GET /monitoring/status` - System status
- `GET /monitoring/alerts` - Active alerts
- `POST /monitoring/alert/{id}/resolve` - Resolve alert

#### System Management  
- `POST /system/healing/{action}` - Trigger healing action
- `GET /system/services` - Service statuses

#### AI Integration
- `POST /ai/chat` - Chat with AI using memory

### Example Usage

```python
import requests

# Store a memory
response = requests.post("http://localhost:8080/memory/store", json={
    "content": "User prefers Python for data analysis tasks",
    "source": "user",
    "tags": ["preference", "programming"]
})

# Query memories
response = requests.post("http://localhost:8080/memory/query", json={
    "query": "python programming",
    "n_results": 5
})

# Check system health
response = requests.get("http://localhost:8080/health")
print(response.json())
```

### Direct Component Usage

```python
# Use memory system directly
from memory_system import PersistentMemorySystem

memory = PersistentMemorySystem()
memory_id = memory.store_memory("Important information", source="user")
results = memory.retrieve_memories("information")

# Use monitoring system directly  
from monitoring_system import MonitoringSystem

monitor = MonitoringSystem()
status = monitor.get_system_status()
```

## 🔍 Monitoring & Metrics

### Prometheus Metrics
Access metrics at: `http://localhost:8000/metrics`

Key metrics:
- `system_cpu_usage_percent` - CPU usage
- `system_memory_usage_percent` - Memory usage  
- `system_disk_usage_percent` - Disk usage
- `ollama_service_status` - Ollama status
- `redis_service_status` - Redis status
- `postgres_service_status` - PostgreSQL status

### Health Checks
- System resource monitoring (CPU, RAM, disk)
- Service availability checks (Ollama, Redis, PostgreSQL, Docker)
- Container status monitoring (AnythingLLM)
- Automatic recovery actions

### Alerting
- Email notifications via SMTP
- Webhook notifications
- Configurable alert thresholds
- Alert history and resolution tracking

## 🛠️ Configuration

Edit `config.yaml` to customize:

```yaml
system:
  name: "Ultimate AI DevOps System"
  
api:
  host: "0.0.0.0"
  port: 8080
  
memory:
  vector_store:
    provider: "chromadb"
    embedding_model: "all-MiniLM-L6-v2"
    
monitoring:
  health_checks:
    cpu_threshold: 90.0
    memory_threshold: 90.0
```

### Environment Variables

```bash
# SMTP Configuration
export SMTP_USERNAME="your-email@example.com"
export SMTP_PASSWORD="your-app-password"
export ALERT_FROM_EMAIL="alerts@yourcompany.com"
export ALERT_TO_EMAILS="admin@yourcompany.com,ops@yourcompany.com"

# Webhook Configuration  
export ALERT_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

## 🔧 Auto-Healing Actions

The system includes intelligent auto-healing:

- **Service Recovery**: Automatic restart of failed services
- **Container Management**: Docker container restart and recovery
- **Cache Clearing**: Automatic cache cleanup on memory issues
- **Disk Cleanup**: Automated disk space management
- **Process Management**: Stuck process detection and cleanup

Available healing actions:
- `restart_service` - Restart systemd services
- `restart_container` - Restart Docker containers  
- `clear_cache` - Clear Redis/system caches
- `cleanup_disk_space` - Free up disk space
- `restart_ollama` - Restart Ollama service
- `restart_redis` - Restart Redis service
- `restart_postgres` - Restart PostgreSQL service

## 🎤 Voice Control (Whisper)

Voice commands are processed using OpenAI Whisper:

```python
# Voice control integration
import whisper
import sounddevice as sd

model = whisper.load_model("base")
# Process audio input and convert to text commands
```

## 📊 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │    │  Memory System  │    │ Monitoring Sys  │
│                 │    │                 │    │                 │
│  - REST API     │◄──►│  - ChromaDB     │◄──►│  - Health Check │
│  - WebSocket    │    │  - pgvector     │    │  - Auto Healing │
│  - Auth         │    │  - Redis Cache  │    │  - Alerting     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Services   │    │   Data Layer    │    │   Infrastructure│
│                 │    │                 │    │                 │
│  - Ollama       │    │  - PostgreSQL   │    │  - Docker       │
│  - OpenAI API   │    │  - Redis        │    │  - AnythingLLM  │  
│  - Whisper      │    │  - ChromaDB     │    │  - Prometheus   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔒 Security

- API authentication and authorization
- Database connection security
- Container isolation
- Environment variable protection
- Service account management
- Network security policies

## 📚 API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

## 🚨 Troubleshooting

### Common Issues

1. **Services not starting**
   ```bash
   sudo systemctl status ollama redis-server postgresql docker
   ```

2. **Memory system errors**
   ```bash
   # Check Redis connection
   redis-cli ping
   
   # Check PostgreSQL connection
   sudo -u postgres psql -c "SELECT version();"
   ```

3. **Container issues**
   ```bash
   docker logs anythingllm-container
   docker restart anythingllm-container
   ```

4. **Permission issues**
   ```bash
   sudo usermod -aG docker $USER
   sudo chown -R $USER:$USER ~/.anythingllm
   ```

### Log Files

- System logs: `logs/ai_devops.log`
- Service logs: `journalctl -u ollama -f`
- Container logs: `docker logs anythingllm-container`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋 Support

For issues and questions:
- Check the troubleshooting section
- Review system logs
- Open an issue on GitHub
- Contact the development team

---

**Built with ❤️ for the AI DevOps community**