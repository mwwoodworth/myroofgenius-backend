FROM node:20-alpine

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    postgresql-client \
    curl \
    git

# Create app directory
WORKDIR /app

# Create package.json for local MCP gateway
COPY package.json /app/package.json
RUN npm install

# Copy application code
COPY mcp-config.json /app/config.json
COPY startup.sh /app/startup.sh
COPY health-server.js /app/health-server.js
COPY mcp-gateway.js /app/mcp-gateway.js
RUN chmod +x /app/startup.sh

# Expose ports
EXPOSE 8080 8081

# Set environment
ENV NODE_ENV=production
ENV MCP_CONFIG=/app/config.json

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Start MCP gateway and health server
CMD ["/app/startup.sh"]