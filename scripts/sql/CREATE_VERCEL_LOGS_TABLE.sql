-- Create Vercel logs table for frontend observability
CREATE TABLE IF NOT EXISTS vercel_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    type VARCHAR(50) NOT NULL,
    level VARCHAR(20) NOT NULL,
    message TEXT,
    source VARCHAR(50),
    environment VARCHAR(50) DEFAULT 'production',
    project_name VARCHAR(100),
    deployment_id VARCHAR(100),
    request_id VARCHAR(100),
    path VARCHAR(500),
    status_code INTEGER,
    method VARCHAR(10),
    user_agent TEXT,
    ip_address VARCHAR(50),
    duration_ms INTEGER,
    memory_used_mb INTEGER,
    error_message TEXT,
    error_stack TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_vercel_logs_timestamp_type ON vercel_logs(timestamp, type);
CREATE INDEX idx_vercel_logs_error_lookup ON vercel_logs(timestamp, level, status_code);
CREATE INDEX idx_vercel_logs_performance ON vercel_logs(timestamp, duration_ms);
CREATE INDEX idx_vercel_logs_deployment ON vercel_logs(deployment_id);
CREATE INDEX idx_vercel_logs_path ON vercel_logs(path);
CREATE INDEX idx_vercel_logs_ip ON vercel_logs(ip_address);

-- Create alert rules table
CREATE TABLE IF NOT EXISTS vercel_alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    condition_type VARCHAR(50) NOT NULL, -- error_rate, build_failure, performance, security
    threshold_value INTEGER NOT NULL,
    threshold_window_minutes INTEGER DEFAULT 60,
    alert_channels JSONB, -- {slack: true, email: true, webhook: "url"}
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default alert rules
INSERT INTO vercel_alert_rules (name, condition_type, threshold_value, alert_channels) VALUES
('High Error Rate', 'error_rate', 50, '{"slack": true, "email": false}'),
('Build Failures', 'build_failure', 1, '{"slack": true, "email": true}'),
('Slow Response Time', 'performance', 3000, '{"slack": true, "email": false}'),
('Security Threats', 'security', 10, '{"slack": true, "email": true}');