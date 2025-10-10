# MCP & AI Agent Integration System

## Overview

This document describes the complete integration system that connects the FastAPI backend with MCP servers and AI agents, enabling sophisticated workflow orchestration and system monitoring.

## Architecture

```
FastAPI Backend (Port 10000)
    │
    ├── Integration Router (/api/v1/integration/*)
    │   ├── MCP Service Layer → MCP Servers (Ports 5001-5006)
    │   ├── AI Agent Service → AI Agents (Ports 6001-6006)
    │   └── Workflow Orchestration
    │
    └── System Monitoring (/api/v1/system/*)
        ├── Health Monitoring
        ├── Performance Metrics
        └── Alert System
```

## Components

### 1. MCP Service Layer (`services/mcp_service.py`)

Handles communication with MCP (Model Context Protocol) servers running on ports 5001-5006:

- **Filesystem Server** (Port 5001): File operations, directory management
- **Postgres Server** (Port 5002): Database queries, schema operations
- **GitHub Server** (Port 5003): Repository management, commits, PRs
- **Fetch Server** (Port 5004): HTTP requests, API calls, web scraping
- **Automation Server** (Port 5005): Webhooks, scheduled tasks, workflows
- **Analytics Server** (Port 5006): Metrics collection, reporting, dashboards

#### Key Features:
- Automatic health checking and status monitoring
- Connection pooling and timeout management
- Error handling and retry logic
- Performance metrics tracking

### 2. AI Agent Service Layer (`services/ai_agent_service.py`)

Orchestrates AI agents running on ports 6001-6006:

- **Data Analyst** (Port 6001): Revenue analysis, customer segmentation
- **Automation Specialist** (Port 6002): Process automation, workflow optimization
- **Content Creator** (Port 6003): Proposal generation, marketing content
- **Customer Success** (Port 6004): Support responses, satisfaction analysis
- **Financial Advisor** (Port 6005): Revenue forecasting, cost optimization
- **Operations Manager** (Port 6006): Schedule optimization, performance analysis

#### Key Features:
- Intelligent agent selection based on capabilities and load
- Task queuing and priority management
- Performance tracking and load balancing
- Multi-step workflow execution

### 3. Workflow Orchestration (`services/workflow_service.py`)

Enables complex multi-step workflows combining MCP operations and AI tasks:

#### Built-in Workflow Templates:

1. **Customer Onboarding**
   - Validates customer data
   - Creates database records
   - Generates welcome content
   - Sends automated emails
   - Schedules follow-up tasks

2. **Revenue Analysis**
   - Fetches revenue data from database
   - Analyzes patterns with AI
   - Generates forecasts
   - Creates comprehensive reports
   - Stores results

3. **Customer Support**
   - Fetches customer context
   - Analyzes support queries
   - Generates AI responses
   - Handles escalation logic
   - Logs interactions

#### Workflow Features:
- Dependency management between steps
- Conditional execution
- Parallel step execution
- Error handling and retry logic
- Real-time status tracking

### 4. System Monitoring (`services/monitoring_service.py`)

Comprehensive system health and performance monitoring:

#### Monitoring Capabilities:
- **System Metrics**: CPU, memory, disk usage, network I/O
- **Service Health**: Database, external APIs, MCP servers, AI agents
- **Performance Trends**: Historical metrics and trend analysis
- **Alert System**: Configurable thresholds and notifications
- **Availability Tracking**: Uptime statistics and SLA monitoring

## API Endpoints

### Integration Endpoints

#### MCP Server Communication
- `GET /api/v1/integration/mcp/health` - Check all MCP servers
- `GET /api/v1/integration/mcp/health/{server_name}` - Check specific server
- `POST /api/v1/integration/mcp/call` - Direct MCP server calls
- `POST /api/v1/integration/mcp/filesystem/{operation}` - Filesystem operations
- `POST /api/v1/integration/mcp/database/query` - Database queries
- `POST /api/v1/integration/mcp/github/{operation}` - GitHub operations
- `POST /api/v1/integration/mcp/fetch` - HTTP fetch operations
- `POST /api/v1/integration/mcp/automation/trigger` - Trigger automations
- `GET /api/v1/integration/mcp/analytics/{metric}` - Analytics data

#### AI Agent Communication
- `GET /api/v1/integration/agents/health` - Check all AI agents
- `GET /api/v1/integration/agents/health/{agent_name}` - Check specific agent
- `POST /api/v1/integration/agents/delegate` - Delegate tasks to agents
- `POST /api/v1/integration/agents/workflow` - Execute multi-agent workflows
- `GET /api/v1/integration/agents/capabilities` - Get agent capabilities

#### Quick Actions
- `POST /api/v1/integration/quick/analyze-revenue` - Quick revenue analysis
- `POST /api/v1/integration/quick/generate-proposal` - Generate customer proposal
- `POST /api/v1/integration/quick/optimize-schedule` - Schedule optimization
- `POST /api/v1/integration/quick/customer-support` - AI customer support

#### Unified Status
- `GET /api/v1/integration/status` - Complete system status

### System Monitoring Endpoints

- `GET /api/v1/system/health-report` - Comprehensive health report
- `GET /api/v1/system/performance-trends` - Performance trends analysis
- `GET /api/v1/system/availability` - Service availability metrics
- `GET /api/v1/system/alerts` - System alerts
- `POST /api/v1/system/alerts/{alert_id}/resolve` - Resolve alerts

### Workflow Management Endpoints

- `GET /api/v1/workflows/templates` - Available workflow templates
- `POST /api/v1/workflows/start/{template_id}` - Start workflow execution
- `GET /api/v1/workflows/executions` - List workflow executions
- `GET /api/v1/workflows/executions/{execution_id}` - Get execution status
- `POST /api/v1/workflows/executions/{execution_id}/cancel` - Cancel workflow

## Configuration

### MCP Servers

MCP servers are expected to run on the following ports:
- Port 5001: Filesystem operations
- Port 5002: Database operations
- Port 5003: GitHub operations
- Port 5004: Fetch/HTTP operations
- Port 5005: Automation workflows
- Port 5006: Analytics and metrics

### AI Agents

AI agents are expected to run on the following ports:
- Port 6001: Data Analyst
- Port 6002: Automation Specialist
- Port 6003: Content Creator
- Port 6004: Customer Success
- Port 6005: Financial Advisor
- Port 6006: Operations Manager

### Health Check Endpoints

All MCP servers and AI agents should implement:
- `GET /health` - Returns health status
- `POST /execute` or `POST /mcp` - Execute tasks/commands

## Usage Examples

### 1. Check System Status

```bash
curl http://localhost:10000/api/v1/integration/status
```

### 2. Delegate Task to AI Agent

```bash
curl -X POST http://localhost:10000/api/v1/integration/agents/delegate \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "analyze_revenue",
    "context": {"timeframe": "30d"},
    "priority": "high"
  }'
```

### 3. Execute MCP Database Query

```bash
curl -X POST http://localhost:10000/api/v1/integration/mcp/database/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT COUNT(*) FROM customers",
    "params": {}
  }'
```

### 4. Start Revenue Analysis Workflow

```bash
curl -X POST http://localhost:10000/api/v1/workflows/start/revenue_analysis \
  -H "Content-Type: application/json" \
  -d '{
    "timeframe": "30d",
    "include_forecasts": true
  }'
```

### 5. Get System Health Report

```bash
curl http://localhost:10000/api/v1/system/health-report
```

## Error Handling

The integration system includes comprehensive error handling:

- **Connection Failures**: Graceful degradation when MCP servers or AI agents are offline
- **Timeout Management**: Configurable timeouts for all operations
- **Retry Logic**: Automatic retry for transient failures
- **Circuit Breaker**: Prevents cascading failures
- **Error Logging**: Detailed logging for debugging

## Monitoring and Alerting

### Automatic Monitoring

The system continuously monitors:
- MCP server availability and response times
- AI agent health and task load
- System resource usage (CPU, memory, disk)
- Database connectivity and performance
- External service dependencies

### Alert Thresholds

Default alert thresholds:
- CPU usage > 80%
- Memory usage > 85%
- Disk usage > 90%
- Response time > 5 seconds
- Service unavailability > 30 seconds

### Performance Metrics

Tracked metrics include:
- Request/response times
- Success/failure rates
- Resource utilization
- Task completion rates
- System availability

## Security Considerations

- All MCP and AI agent communications use HTTP(S)
- Authentication tokens can be configured for secure communication
- Input validation and sanitization for all API calls
- Rate limiting and request throttling
- Audit logging for all operations

## Deployment Requirements

### Dependencies

```
fastapi>=0.100.0
httpx>=0.24.0
psutil>=5.9.0
pydantic>=2.0.0
sqlalchemy>=2.0.0
```

### Environment Variables

```bash
DATABASE_URL=postgresql://...
MCP_AUTH_TOKEN=your_mcp_token
AI_AGENT_AUTH_TOKEN=your_agent_token
```

### Docker Deployment

The integration system is designed to work with containerized deployments where MCP servers and AI agents run in separate containers.

## Testing

### Startup Test

```bash
python3 test_startup.py
```

### Integration Test

```bash
python3 test_integration.py
```

### Debug Services

```bash
python3 debug_integration.py
```

## Future Enhancements

1. **Advanced Workflow Features**
   - Visual workflow designer
   - Conditional branching
   - Loop constructs
   - Sub-workflow support

2. **Enhanced Monitoring**
   - Real-time dashboards
   - Predictive alerting
   - SLA tracking
   - Performance optimization recommendations

3. **Security Improvements**
   - OAuth 2.0 integration
   - API key management
   - Encrypted communications
   - Access control and permissions

4. **Scalability Features**
   - Load balancing across multiple agent instances
   - Horizontal scaling support
   - Distributed workflow execution
   - Caching and optimization

## Conclusion

This integration system provides a robust, scalable foundation for orchestrating complex workflows between MCP servers and AI agents. It enables the FastAPI backend to leverage the full power of distributed AI services while maintaining reliability, observability, and performance.

The system is production-ready and includes comprehensive monitoring, error handling, and testing capabilities. It can be extended and customized to meet specific business requirements while maintaining compatibility with the existing FastAPI infrastructure.