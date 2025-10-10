-- ============================================================================
-- DevOps Observability Tables for Render and Vercel
-- ============================================================================

-- Deployment events from webhooks
CREATE TABLE IF NOT EXISTS deployment_events (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,  -- 'render' or 'vercel'
    event_type VARCHAR(100) NOT NULL,
    payload JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    
    -- Indexes for performance
    CONSTRAINT deployment_events_unique UNIQUE (platform, event_type, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_deployment_events_platform ON deployment_events(platform);
CREATE INDEX IF NOT EXISTS idx_deployment_events_timestamp ON deployment_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_deployment_events_event_type ON deployment_events(event_type);

-- Vercel log entries
CREATE TABLE IF NOT EXISTS vercel_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    level VARCHAR(20),  -- 'info', 'warning', 'error', 'fatal'
    message TEXT,
    source VARCHAR(100),
    deployment_id VARCHAR(255),
    request_id VARCHAR(255),
    path VARCHAR(500),
    status_code INTEGER,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent duplicate log entries
    CONSTRAINT vercel_logs_unique UNIQUE (timestamp, request_id, message)
);

CREATE INDEX IF NOT EXISTS idx_vercel_logs_timestamp ON vercel_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_vercel_logs_level ON vercel_logs(level);
CREATE INDEX IF NOT EXISTS idx_vercel_logs_deployment_id ON vercel_logs(deployment_id);
CREATE INDEX IF NOT EXISTS idx_vercel_logs_request_id ON vercel_logs(request_id);

-- Render service metrics
CREATE TABLE IF NOT EXISTS render_metrics (
    id SERIAL PRIMARY KEY,
    service_id VARCHAR(255) NOT NULL,
    metric_type VARCHAR(100) NOT NULL,  -- 'cpu', 'memory', 'disk', 'bandwidth'
    value DECIMAL(10,2),
    unit VARCHAR(20),  -- 'percent', 'MB', 'GB', 'Mbps'
    timestamp TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT render_metrics_unique UNIQUE (service_id, metric_type, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_render_metrics_service ON render_metrics(service_id);
CREATE INDEX IF NOT EXISTS idx_render_metrics_timestamp ON render_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_render_metrics_type ON render_metrics(metric_type);

-- Deployment history for tracking
CREATE TABLE IF NOT EXISTS deployment_history (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    deployment_id VARCHAR(255) NOT NULL,
    status VARCHAR(50),  -- 'pending', 'building', 'deploying', 'live', 'failed', 'canceled'
    branch VARCHAR(100),
    commit_sha VARCHAR(100),
    commit_message TEXT,
    triggered_by VARCHAR(255),
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_seconds INTEGER,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT deployment_history_unique UNIQUE (platform, deployment_id)
);

CREATE INDEX IF NOT EXISTS idx_deployment_history_platform ON deployment_history(platform);
CREATE INDEX IF NOT EXISTS idx_deployment_history_status ON deployment_history(status);
CREATE INDEX IF NOT EXISTS idx_deployment_history_started ON deployment_history(started_at DESC);

-- Alerts and incidents
CREATE TABLE IF NOT EXISTS observability_alerts (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50),
    alert_type VARCHAR(100),  -- 'deployment_failed', 'high_error_rate', 'service_down'
    severity VARCHAR(20),  -- 'info', 'warning', 'error', 'critical'
    title VARCHAR(500),
    description TEXT,
    metadata JSONB,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_platform ON observability_alerts(platform);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON observability_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON observability_alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON observability_alerts(resolved);

-- Service health status
CREATE TABLE IF NOT EXISTS service_health (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    status VARCHAR(50),  -- 'healthy', 'degraded', 'down', 'unknown'
    uptime_percent DECIMAL(5,2),
    response_time_ms INTEGER,
    error_rate_percent DECIMAL(5,2),
    last_check TIMESTAMP,
    last_healthy TIMESTAMP,
    metadata JSONB,
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT service_health_unique UNIQUE (service_name, platform)
);

CREATE INDEX IF NOT EXISTS idx_service_health_status ON service_health(status);
CREATE INDEX IF NOT EXISTS idx_service_health_updated ON service_health(updated_at DESC);

-- API usage metrics
CREATE TABLE IF NOT EXISTS api_usage_metrics (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(500) NOT NULL,
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    user_id VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage_metrics(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_status ON api_usage_metrics(status_code);

-- ============================================================================
-- Views for easy querying
-- ============================================================================

-- Recent deployments view
CREATE OR REPLACE VIEW recent_deployments AS
SELECT 
    platform,
    deployment_id,
    status,
    branch,
    commit_sha,
    started_at,
    finished_at,
    duration_seconds,
    CASE 
        WHEN status = 'live' THEN 'success'
        WHEN status IN ('failed', 'error') THEN 'failure'
        WHEN status IN ('canceled', 'cancelled') THEN 'canceled'
        ELSE 'in_progress'
    END as result
FROM deployment_history
WHERE started_at > NOW() - INTERVAL '7 days'
ORDER BY started_at DESC;

-- Error rate view
CREATE OR REPLACE VIEW error_rates AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) FILTER (WHERE level IN ('error', 'fatal')) as error_count,
    COUNT(*) as total_logs,
    ROUND(
        COUNT(*) FILTER (WHERE level IN ('error', 'fatal'))::NUMERIC / 
        NULLIF(COUNT(*), 0) * 100, 
        2
    ) as error_rate_percent
FROM vercel_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

-- Service health summary
CREATE OR REPLACE VIEW service_health_summary AS
SELECT 
    platform,
    COUNT(*) as total_services,
    COUNT(*) FILTER (WHERE status = 'healthy') as healthy,
    COUNT(*) FILTER (WHERE status = 'degraded') as degraded,
    COUNT(*) FILTER (WHERE status = 'down') as down,
    AVG(uptime_percent) as avg_uptime,
    AVG(response_time_ms) as avg_response_time,
    AVG(error_rate_percent) as avg_error_rate
FROM service_health
GROUP BY platform;

-- ============================================================================
-- Stored procedures for maintenance
-- ============================================================================

-- Clean up old logs (keep 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM vercel_logs WHERE timestamp < NOW() - INTERVAL '30 days';
    DELETE FROM deployment_events WHERE timestamp < NOW() - INTERVAL '30 days';
    DELETE FROM api_usage_metrics WHERE timestamp < NOW() - INTERVAL '30 days';
    DELETE FROM render_metrics WHERE timestamp < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- Calculate deployment success rate
CREATE OR REPLACE FUNCTION get_deployment_success_rate(
    p_platform VARCHAR DEFAULT NULL,
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE(
    platform VARCHAR,
    total_deployments BIGINT,
    successful BIGINT,
    failed BIGINT,
    success_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dh.platform,
        COUNT(*) as total_deployments,
        COUNT(*) FILTER (WHERE dh.status = 'live') as successful,
        COUNT(*) FILTER (WHERE dh.status IN ('failed', 'error')) as failed,
        ROUND(
            COUNT(*) FILTER (WHERE dh.status = 'live')::NUMERIC / 
            NULLIF(COUNT(*), 0) * 100, 
            2
        ) as success_rate
    FROM deployment_history dh
    WHERE 
        (p_platform IS NULL OR dh.platform = p_platform)
        AND dh.started_at > NOW() - (p_days || ' days')::INTERVAL
    GROUP BY dh.platform;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Grant permissions
-- ============================================================================

-- Grant permissions to the application user
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- ============================================================================
-- Initial data
-- ============================================================================

-- Insert initial service health records
INSERT INTO service_health (service_name, platform, status, uptime_percent, response_time_ms, error_rate_percent, last_check, last_healthy)
VALUES 
    ('brainops-backend', 'render', 'healthy', 99.9, 150, 0.1, NOW(), NOW()),
    ('myroofgenius-app', 'vercel', 'healthy', 99.95, 80, 0.05, NOW(), NOW()),
    ('weathercraft-erp', 'vercel', 'healthy', 99.8, 120, 0.2, NOW(), NOW()),
    ('brainops-task-os', 'vercel', 'healthy', 99.9, 100, 0.1, NOW(), NOW())
ON CONFLICT (service_name, platform) DO UPDATE
SET 
    status = EXCLUDED.status,
    last_check = NOW(),
    updated_at = NOW();

-- ============================================================================
COMMIT;