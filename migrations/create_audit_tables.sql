-- ============================================================================
-- Audit Logging Tables
-- Comprehensive audit trail for compliance and security
-- ============================================================================

-- Main audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    user_id UUID,
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB,
    severity VARCHAR(20) DEFAULT 'INFO',
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path TEXT,
    created_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for performance
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for efficient querying
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_severity ON audit_logs(severity);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_details_gin ON audit_logs USING gin(details);

-- Data change audit table (for tracking actual data changes)
CREATE TABLE IF NOT EXISTS data_audit_trail (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    operation VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    user_id UUID,
    old_data JSONB,
    new_data JSONB,
    changed_fields TEXT[],
    change_timestamp TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_data_audit_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_data_audit_table ON data_audit_trail(table_name);
CREATE INDEX idx_data_audit_record ON data_audit_trail(record_id);
CREATE INDEX idx_data_audit_user ON data_audit_trail(user_id);
CREATE INDEX idx_data_audit_timestamp ON data_audit_trail(change_timestamp DESC);

-- API request/response logging
CREATE TABLE IF NOT EXISTS api_audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    request_id VARCHAR(100) UNIQUE,
    user_id UUID,
    method VARCHAR(10) NOT NULL,
    path TEXT NOT NULL,
    query_params JSONB,
    request_body JSONB,
    response_status INTEGER,
    response_body JSONB,
    response_time_ms FLOAT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_api_audit_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_api_audit_user ON api_audit_logs(user_id);
CREATE INDEX idx_api_audit_path ON api_audit_logs(path);
CREATE INDEX idx_api_audit_status ON api_audit_logs(response_status);
CREATE INDEX idx_api_audit_created ON api_audit_logs(created_at DESC);

-- Security events table
CREATE TABLE IF NOT EXISTS security_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL, -- LOGIN_FAILED, PERMISSION_DENIED, etc.
    severity VARCHAR(20) NOT NULL, -- INFO, WARNING, ERROR, CRITICAL
    user_id UUID,
    details JSONB NOT NULL,
    ip_address INET,
    user_agent TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID,
    resolved_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_security_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_security_resolved_by FOREIGN KEY (resolved_by)
        REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_security_events_user ON security_events(user_id);
CREATE INDEX idx_security_events_type ON security_events(event_type);
CREATE INDEX idx_security_events_severity ON security_events(severity);
CREATE INDEX idx_security_events_created ON security_events(created_at DESC);
CREATE INDEX idx_security_events_resolved ON security_events(resolved);

-- ============================================================================
-- AUDIT TRIGGERS
-- ============================================================================

-- Generic audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    audit_user_id UUID;
    old_data JSONB;
    new_data JSONB;
    changed_fields TEXT[];
BEGIN
    -- Get current user from context
    BEGIN
        audit_user_id := current_setting('app.current_user_id')::UUID;
    EXCEPTION
        WHEN OTHERS THEN
            audit_user_id := NULL;
    END;

    -- Prepare data based on operation
    IF TG_OP = 'DELETE' THEN
        old_data := to_jsonb(OLD);
        new_data := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        old_data := to_jsonb(OLD);
        new_data := to_jsonb(NEW);

        -- Calculate changed fields
        SELECT array_agg(key) INTO changed_fields
        FROM jsonb_each(old_data) old_kv
        FULL OUTER JOIN jsonb_each(new_data) new_kv
            ON old_kv.key = new_kv.key
        WHERE old_kv.value IS DISTINCT FROM new_kv.value;
    ELSIF TG_OP = 'INSERT' THEN
        old_data := NULL;
        new_data := to_jsonb(NEW);
    END IF;

    -- Insert audit record
    INSERT INTO data_audit_trail (
        table_name,
        record_id,
        operation,
        user_id,
        old_data,
        new_data,
        changed_fields,
        change_timestamp
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        audit_user_id,
        old_data,
        new_data,
        changed_fields,
        NOW()
    );

    -- Return appropriate value
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to critical tables
CREATE TRIGGER audit_customers
    AFTER INSERT OR UPDATE OR DELETE ON customers
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_jobs
    AFTER INSERT OR UPDATE OR DELETE ON jobs
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_invoices
    AFTER INSERT OR UPDATE OR DELETE ON invoices
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_estimates
    AFTER INSERT OR UPDATE OR DELETE ON estimates
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_users
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- ============================================================================
-- AUDIT REPORTING VIEWS
-- ============================================================================

-- User activity summary view
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT
    u.id as user_id,
    u.email,
    u.role,
    COUNT(DISTINCT al.id) as total_events,
    COUNT(DISTINCT CASE WHEN al.event_type = 'AUTH' THEN al.id END) as auth_events,
    COUNT(DISTINCT CASE WHEN al.event_type = 'DATA' THEN al.id END) as data_events,
    COUNT(DISTINCT CASE WHEN al.severity IN ('ERROR', 'CRITICAL') THEN al.id END) as error_events,
    MAX(al.created_at) as last_activity
FROM users u
LEFT JOIN audit_logs al ON u.id = al.user_id
GROUP BY u.id, u.email, u.role;

-- Daily audit summary
CREATE OR REPLACE VIEW daily_audit_summary AS
SELECT
    DATE(created_at) as audit_date,
    event_type,
    severity,
    COUNT(*) as event_count,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT ip_address) as unique_ips
FROM audit_logs
GROUP BY DATE(created_at), event_type, severity
ORDER BY audit_date DESC, event_count DESC;

-- ============================================================================
-- CLEANUP POLICIES
-- ============================================================================

-- Function to archive old audit logs
CREATE OR REPLACE FUNCTION archive_old_audit_logs(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Move old logs to archive table (create if needed)
    CREATE TABLE IF NOT EXISTS audit_logs_archive (LIKE audit_logs INCLUDING ALL);

    INSERT INTO audit_logs_archive
    SELECT * FROM audit_logs
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;

    GET DIAGNOSTICS archived_count = ROW_COUNT;

    -- Delete from main table
    DELETE FROM audit_logs
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;

    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

GRANT SELECT ON audit_logs TO authenticated;
GRANT SELECT ON user_activity_summary TO authenticated;
GRANT SELECT ON daily_audit_summary TO authenticated;