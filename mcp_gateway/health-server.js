const http = require('http');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

// Health check server for MCP Gateway
const PORT = 8081;

// Track gateway status
let gatewayStatus = {
  status: 'starting',
  lastCheck: new Date().toISOString(),
  uptime: 0,
  servers: {},
  errors: []
};

// Check if MCP servers are running
async function checkMCPServers() {
  const servers = ['filesystem', 'postgres', 'github', 'fetch'];
  const serverStatus = {};
  
  for (const server of servers) {
    try {
      // Check if process is running
      const { stdout } = await execPromise(`pgrep -f "mcp-server-${server}" | head -1`);
      serverStatus[server] = {
        status: stdout.trim() ? 'running' : 'stopped',
        pid: stdout.trim() || null
      };
    } catch (error) {
      serverStatus[server] = {
        status: 'stopped',
        pid: null
      };
    }
  }
  
  return serverStatus;
}

// Check gateway main process
async function checkGateway() {
  try {
    const { stdout } = await execPromise('pgrep -f "mcp-gateway" | head -1');
    return {
      running: !!stdout.trim(),
      pid: stdout.trim() || null
    };
  } catch (error) {
    return {
      running: false,
      pid: null
    };
  }
}

// Update status periodically
async function updateStatus() {
  try {
    const gateway = await checkGateway();
    const servers = await checkMCPServers();
    
    const allServersRunning = Object.values(servers).every(s => s.status === 'running');
    
    gatewayStatus = {
      status: gateway.running && allServersRunning ? 'healthy' : 'degraded',
      lastCheck: new Date().toISOString(),
      uptime: process.uptime(),
      gateway: gateway,
      servers: servers,
      errors: gatewayStatus.errors.slice(-10) // Keep last 10 errors
    };
  } catch (error) {
    gatewayStatus.errors.push({
      timestamp: new Date().toISOString(),
      message: error.message
    });
    gatewayStatus.status = 'error';
  }
}

// Create HTTP server for health checks
const server = http.createServer(async (req, res) => {
  // Update status before responding
  await updateStatus();
  
  if (req.url === '/health') {
    const isHealthy = gatewayStatus.status === 'healthy';
    res.writeHead(isHealthy ? 200 : 503, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      healthy: isHealthy,
      ...gatewayStatus
    }));
  } else if (req.url === '/metrics') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      cpu: process.cpuUsage(),
      ...gatewayStatus
    }));
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
  }
});

// Start server
server.listen(PORT, () => {
  console.log(`🏥 Health check server running on port ${PORT}`);
  console.log(`📊 Health endpoint: http://localhost:${PORT}/health`);
  console.log(`📈 Metrics endpoint: http://localhost:${PORT}/metrics`);
});

// Update status every 10 seconds
setInterval(updateStatus, 10000);

// Initial status update
updateStatus();

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('🛑 Health server shutting down...');
  server.close(() => {
    process.exit(0);
  });
});