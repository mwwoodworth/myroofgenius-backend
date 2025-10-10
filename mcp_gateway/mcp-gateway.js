const express = require('express');
const axios = require('axios');
const { Pool } = require('pg');
const cors = require('cors');
const bodyParser = require('body-parser');
const helmet = require('helmet');
const winston = require('winston');
const fs = require('fs');
const path = require('path');

// Logger setup
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Load configuration
const configPath = process.env.MCP_CONFIG || './config.json';
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

// Create Express app
const app = express();
const port = process.env.PORT || config.gateway?.port || 8080;
const adminPort = process.env.ADMIN_PORT || config.gateway?.adminPort || 8081;

// Middleware
app.use(helmet());
app.use(cors(config.gateway?.cors || { origin: '*' }));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Database connection
const dbUrl = process.env.DATABASE_URL || config.servers?.postgres?.env?.DATABASE_URL;
const pool = dbUrl ? new Pool({ connectionString: dbUrl }) : null;

// MCP Server Registry
const mcpServers = {
  filesystem: {
    name: 'Filesystem Server',
    status: 'ready',
    capabilities: ['read', 'write', 'list', 'search']
  },
  postgres: {
    name: 'PostgreSQL Server',
    status: pool ? 'ready' : 'unavailable',
    capabilities: ['query', 'execute', 'transaction']
  },
  github: {
    name: 'GitHub Server',
    status: 'ready',
    capabilities: ['repos', 'issues', 'pulls', 'actions']
  },
  fetch: {
    name: 'Fetch Server',
    status: 'ready',
    capabilities: ['http', 'websocket']
  }
};

// Health check endpoint
app.get('/health', (req, res) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    servers: mcpServers,
    uptime: process.uptime()
  };
  res.json(health);
});

// List available MCP servers
app.get('/api/servers', (req, res) => {
  res.json({
    servers: Object.entries(mcpServers).map(([key, server]) => ({
      id: key,
      ...server
    }))
  });
});

// Execute filesystem operation
app.post('/api/filesystem/:operation', async (req, res) => {
  try {
    const { operation } = req.params;
    const { path: filePath, content } = req.body;
    
    logger.info(`Filesystem operation: ${operation} on ${filePath}`);
    
    switch (operation) {
      case 'read':
        const data = fs.readFileSync(filePath, 'utf8');
        res.json({ success: true, data });
        break;
      case 'write':
        fs.writeFileSync(filePath, content);
        res.json({ success: true });
        break;
      case 'list':
        const files = fs.readdirSync(filePath);
        res.json({ success: true, files });
        break;
      default:
        res.status(400).json({ error: 'Invalid operation' });
    }
  } catch (error) {
    logger.error(`Filesystem error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

// Execute database query
app.post('/api/database/query', async (req, res) => {
  if (!pool) {
    return res.status(503).json({ error: 'Database not configured' });
  }
  
  try {
    const { query, params } = req.body;
    logger.info(`Database query: ${query}`);
    
    const result = await pool.query(query, params);
    res.json({
      success: true,
      rows: result.rows,
      rowCount: result.rowCount
    });
  } catch (error) {
    logger.error(`Database error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

// GitHub API proxy
app.post('/api/github/:action', async (req, res) => {
  try {
    const { action } = req.params;
    const { owner, repo, ...params } = req.body;
    const token = process.env.GITHUB_TOKEN || config.servers?.github?.env?.GITHUB_TOKEN;
    
    if (!token) {
      return res.status(503).json({ error: 'GitHub token not configured' });
    }
    
    logger.info(`GitHub action: ${action} on ${owner}/${repo}`);
    
    const githubApi = axios.create({
      baseURL: 'https://api.github.com',
      headers: {
        'Authorization': `token ${token}`,
        'Accept': 'application/vnd.github.v3+json'
      }
    });
    
    let endpoint = '';
    switch (action) {
      case 'repos':
        endpoint = `/repos/${owner}/${repo}`;
        break;
      case 'issues':
        endpoint = `/repos/${owner}/${repo}/issues`;
        break;
      case 'pulls':
        endpoint = `/repos/${owner}/${repo}/pulls`;
        break;
      default:
        return res.status(400).json({ error: 'Invalid action' });
    }
    
    const response = await githubApi.get(endpoint, { params });
    res.json(response.data);
  } catch (error) {
    logger.error(`GitHub error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

// Fetch/HTTP proxy
app.post('/api/fetch', async (req, res) => {
  try {
    const { url, method = 'GET', headers = {}, data } = req.body;
    
    logger.info(`Fetch request: ${method} ${url}`);
    
    const response = await axios({
      url,
      method,
      headers,
      data
    });
    
    res.json({
      success: true,
      status: response.status,
      data: response.data
    });
  } catch (error) {
    logger.error(`Fetch error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

// Operational context integration
app.post('/api/context/update', async (req, res) => {
  if (!pool) {
    return res.status(503).json({ error: 'Database not configured' });
  }
  
  try {
    const { component, status, metrics } = req.body;
    
    await pool.query(`
      INSERT INTO operational_status (component, status, health_score, metrics, last_check)
      VALUES ($1, $2, $3, $4, NOW())
      ON CONFLICT (component) DO UPDATE
      SET status = $2, health_score = $3, metrics = $4, last_check = NOW()
    `, [component, status, metrics.health_score || 0, JSON.stringify(metrics)]);
    
    res.json({ success: true });
  } catch (error) {
    logger.error(`Context update error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

// Task execution logging
app.post('/api/task/log', async (req, res) => {
  if (!pool) {
    return res.status(503).json({ error: 'Database not configured' });
  }
  
  try {
    const { task_name, task_type, status, input_params, output_result } = req.body;
    
    const result = await pool.query(`
      INSERT INTO task_execution_log 
      (task_name, task_type, status, input_params, output_result, started_at)
      VALUES ($1, $2, $3, $4, $5, NOW())
      RETURNING id
    `, [task_name, task_type, status, JSON.stringify(input_params), JSON.stringify(output_result)]);
    
    res.json({ success: true, task_id: result.rows[0].id });
  } catch (error) {
    logger.error(`Task logging error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

// MCP Integration status
app.get('/api/integrations', async (req, res) => {
  if (!pool) {
    return res.status(503).json({ error: 'Database not configured' });
  }
  
  try {
    const result = await pool.query(`
      SELECT service, status, last_sync, error_count
      FROM mcp_integrations
      ORDER BY service
    `);
    
    res.json({
      integrations: result.rows,
      gateway_status: {
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        servers: mcpServers
      }
    });
  } catch (error) {
    logger.error(`Integration status error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

// Start main server
app.listen(port, () => {
  logger.info(`🚀 MCP Gateway running on port ${port}`);
  logger.info(`📡 API endpoints available at http://localhost:${port}/api`);
});

// Admin server for internal health checks
const adminApp = express();
adminApp.get('/health', (req, res) => {
  res.json({
    healthy: true,
    uptime: process.uptime(),
    memory: process.memoryUsage()
  });
});

adminApp.listen(adminPort, () => {
  logger.info(`🏥 Admin server running on port ${adminPort}`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('🛑 Shutting down MCP Gateway...');
  if (pool) {
    await pool.end();
  }
  process.exit(0);
});