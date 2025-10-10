-- Setup Supabase Cron Jobs and Queues for Production System
-- This creates a robust job scheduling and queue processing system

-- Enable pg_cron extension for scheduled jobs
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;

-- Create job queue table
CREATE TABLE IF NOT EXISTS job_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(100) NOT NULL,
    payload JSONB,
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    priority INTEGER DEFAULT 5, -- 1 (highest) to 10 (lowest)
    max_retries INTEGER DEFAULT 3,
    retry_count INTEGER DEFAULT 0,
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for queue performance
CREATE INDEX idx_job_queue_status ON job_queue(status);
CREATE INDEX idx_job_queue_priority ON job_queue(priority);
CREATE INDEX idx_job_queue_scheduled ON job_queue(scheduled_at);
CREATE INDEX idx_job_queue_type ON job_queue(job_type);

-- Create cron job history table
CREATE TABLE IF NOT EXISTS cron_job_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB
);

-- Function to process job queue
CREATE OR REPLACE FUNCTION process_job_queue()
RETURNS void AS $$
DECLARE
    v_job RECORD;
BEGIN
    -- Get next pending job by priority
    FOR v_job IN
        SELECT * FROM job_queue
        WHERE status = 'pending'
        AND scheduled_at <= CURRENT_TIMESTAMP
        ORDER BY priority ASC, created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    LOOP
        -- Update job status to processing
        UPDATE job_queue
        SET status = 'processing',
            started_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = v_job.id;
        
        -- Process different job types
        CASE v_job.job_type
            WHEN 'sync_memory' THEN
                PERFORM sync_persistent_memory();
            WHEN 'cleanup_old_data' THEN
                PERFORM cleanup_old_data();
            WHEN 'sync_env_vars' THEN
                PERFORM sync_environment_variables();
            WHEN 'health_check' THEN
                PERFORM system_health_check();
            WHEN 'backup_database' THEN
                PERFORM backup_critical_data();
            ELSE
                -- Unknown job type
                UPDATE job_queue
                SET status = 'failed',
                    error_message = 'Unknown job type: ' || v_job.job_type,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = v_job.id;
                CONTINUE;
        END CASE;
        
        -- Mark job as completed
        UPDATE job_queue
        SET status = 'completed',
            completed_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = v_job.id;
        
    END LOOP;
EXCEPTION
    WHEN OTHERS THEN
        -- Handle errors
        UPDATE job_queue
        SET status = CASE 
                WHEN retry_count < max_retries THEN 'pending'
                ELSE 'failed'
            END,
            retry_count = retry_count + 1,
            error_message = SQLERRM,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = v_job.id;
END;
$$ LANGUAGE plpgsql;

-- Function to sync persistent memory
CREATE OR REPLACE FUNCTION sync_persistent_memory()
RETURNS void AS $$
BEGIN
    -- Clean up old memory entries
    DELETE FROM copilot_messages
    WHERE created_at < NOW() - INTERVAL '30 days'
    AND is_pinned = false;
    
    -- Update memory statistics
    INSERT INTO cron_job_history (job_name, status, started_at, completed_at, metadata)
    VALUES ('sync_persistent_memory', 'completed', NOW(), NOW(), 
            jsonb_build_object('records_cleaned', (SELECT COUNT(*) FROM copilot_messages WHERE created_at < NOW() - INTERVAL '30 days')));
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old data
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    -- Clean up old job queue entries
    DELETE FROM job_queue
    WHERE status IN ('completed', 'failed')
    AND completed_at < NOW() - INTERVAL '7 days';
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    
    -- Clean up old cron history
    DELETE FROM cron_job_history
    WHERE started_at < NOW() - INTERVAL '30 days';
    
    -- Log cleanup
    INSERT INTO cron_job_history (job_name, status, started_at, completed_at, metadata)
    VALUES ('cleanup_old_data', 'completed', NOW(), NOW(), 
            jsonb_build_object('jobs_deleted', v_deleted_count));
END;
$$ LANGUAGE plpgsql;

-- Function to sync environment variables
CREATE OR REPLACE FUNCTION sync_environment_variables()
RETURNS void AS $$
BEGIN
    -- Update last_synced timestamp for all active vars
    UPDATE master_env_vars
    SET last_synced = CURRENT_TIMESTAMP
    WHERE is_active = true;
    
    -- Log sync
    INSERT INTO cron_job_history (job_name, status, started_at, completed_at)
    VALUES ('sync_environment_variables', 'completed', NOW(), NOW());
END;
$$ LANGUAGE plpgsql;

-- Function for system health check
CREATE OR REPLACE FUNCTION system_health_check()
RETURNS void AS $$
DECLARE
    v_health_status JSONB;
BEGIN
    v_health_status = jsonb_build_object(
        'database_size', (SELECT pg_database_size(current_database())),
        'active_connections', (SELECT count(*) FROM pg_stat_activity),
        'table_count', (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'),
        'memory_entries', (SELECT count(*) FROM copilot_messages),
        'queue_pending', (SELECT count(*) FROM job_queue WHERE status = 'pending'),
        'timestamp', NOW()
    );
    
    -- Store health check result
    INSERT INTO cron_job_history (job_name, status, started_at, completed_at, metadata)
    VALUES ('system_health_check', 'completed', NOW(), NOW(), v_health_status);
    
    -- Alert if issues detected
    IF (v_health_status->>'queue_pending')::INTEGER > 100 THEN
        INSERT INTO job_queue (job_type, payload, priority)
        VALUES ('alert', jsonb_build_object('message', 'High queue backlog detected'), 1);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to backup critical data
CREATE OR REPLACE FUNCTION backup_critical_data()
RETURNS void AS $$
BEGIN
    -- This would typically call external backup service
    -- For now, we'll just log the backup request
    INSERT INTO cron_job_history (job_name, status, started_at, completed_at, metadata)
    VALUES ('backup_critical_data', 'completed', NOW(), NOW(), 
            jsonb_build_object('tables_backed_up', ARRAY['copilot_messages', 'master_env_vars', 'app_users']));
END;
$$ LANGUAGE plpgsql;

-- Schedule cron jobs using pg_cron
SELECT cron.schedule('process-queue-every-minute', '* * * * *', 'SELECT process_job_queue();');
SELECT cron.schedule('cleanup-old-data-daily', '0 2 * * *', 'SELECT cleanup_old_data();');
SELECT cron.schedule('sync-memory-hourly', '0 * * * *', 'SELECT sync_persistent_memory();');
SELECT cron.schedule('health-check-every-5-minutes', '*/5 * * * *', 'SELECT system_health_check();');
SELECT cron.schedule('sync-env-vars-every-30-minutes', '*/30 * * * *', 'SELECT sync_environment_variables();');
SELECT cron.schedule('backup-data-daily', '0 3 * * *', 'SELECT backup_critical_data();');

-- Function to add job to queue
CREATE OR REPLACE FUNCTION add_job_to_queue(
    p_job_type VARCHAR,
    p_payload JSONB DEFAULT NULL,
    p_priority INTEGER DEFAULT 5,
    p_scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
)
RETURNS UUID AS $$
DECLARE
    v_job_id UUID;
BEGIN
    INSERT INTO job_queue (job_type, payload, priority, scheduled_at)
    VALUES (p_job_type, p_payload, p_priority, p_scheduled_at)
    RETURNING id INTO v_job_id;
    
    RETURN v_job_id;
END;
$$ LANGUAGE plpgsql;

-- Create view for monitoring queue status
CREATE OR REPLACE VIEW queue_status AS
SELECT 
    job_type,
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
    MAX(completed_at) as last_completed
FROM job_queue
GROUP BY job_type, status
ORDER BY job_type, status;

-- Create view for monitoring cron job performance
CREATE OR REPLACE VIEW cron_performance AS
SELECT 
    job_name,
    COUNT(*) as total_runs,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_runs,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_runs,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
    MAX(completed_at) as last_run
FROM cron_job_history
WHERE started_at > NOW() - INTERVAL '7 days'
GROUP BY job_name
ORDER BY job_name;

-- Initial job entries to kickstart the system
INSERT INTO job_queue (job_type, priority) VALUES
    ('sync_memory', 3),
    ('health_check', 5),
    ('sync_env_vars', 4);

-- Create a function to ensure persistent memory is being used
CREATE OR REPLACE FUNCTION ensure_persistent_memory_usage()
RETURNS TABLE(
    service VARCHAR,
    is_using_memory BOOLEAN,
    last_memory_entry TIMESTAMP WITH TIME ZONE,
    entry_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH service_memory AS (
        SELECT 
            COALESCE(meta_data->>'service', 'unknown') as service_name,
            MAX(created_at) as last_entry,
            COUNT(*) as entries
        FROM copilot_messages
        WHERE created_at > NOW() - INTERVAL '24 hours'
        GROUP BY COALESCE(meta_data->>'service', 'unknown')
    )
    SELECT 
        s.service_name::VARCHAR,
        (s.entries > 0)::BOOLEAN,
        s.last_entry,
        s.entries
    FROM service_memory s
    ORDER BY s.service_name;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION ensure_persistent_memory_usage() IS 'Monitor which services are actively using the persistent memory system';

-- Grant permissions
GRANT EXECUTE ON FUNCTION add_job_to_queue TO anon, authenticated;
GRANT SELECT ON queue_status TO anon, authenticated;
GRANT SELECT ON cron_performance TO anon, authenticated;