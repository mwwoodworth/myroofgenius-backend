-- ============================================================================
-- FIX AI BRAIN SCHEMA - Handle existing constraints
-- ============================================================================

-- First, let's check what columns ai_agents actually needs
ALTER TABLE ai_agents 
ADD COLUMN IF NOT EXISTS model VARCHAR(100) DEFAULT 'gpt-4';

-- Now insert missing agents with proper model field
INSERT INTO ai_agents (id, name, type, model, status, capabilities, config) 
VALUES 
    (gen_random_uuid(), 'DeploymentAgent', 'executor', 'gpt-4', 'active', '["deploy", "rollback", "monitor_deployment"]', '{"priority": "high"}'),
    (gen_random_uuid(), 'TestingAgent', 'executor', 'gpt-4', 'active', '["unit_test", "integration_test", "e2e_test"]', '{"coverage_target": 80}'),
    (gen_random_uuid(), 'MonitoringAgent', 'executor', 'gpt-4', 'active', '["monitor", "alert", "diagnose"]', '{"interval": 60}'),
    (gen_random_uuid(), 'SecurityAgent', 'guardian', 'gpt-4', 'active', '["scan", "audit", "protect"]', '{"level": "maximum"}'),
    (gen_random_uuid(), 'ComplianceAgent', 'guardian', 'gpt-4', 'active', '["gdpr", "soc2", "hipaa", "audit"]', '{"strict": true}'),
    (gen_random_uuid(), 'DataAgent', 'analyzer', 'gpt-4', 'active', '["etl", "transform", "analyze", "visualize"]', '{"batch_size": 1000}'),
    (gen_random_uuid(), 'PatternAgent', 'analyzer', 'claude-3', 'active', '["pattern_recognition", "anomaly_detection", "prediction"]', '{"sensitivity": 0.8}'),
    (gen_random_uuid(), 'RevenueAgent', 'analyzer', 'gpt-4', 'active', '["revenue_optimization", "pricing", "forecasting"]', '{"target_growth": 20}'),
    (gen_random_uuid(), 'CustomerAgent', 'specialist', 'claude-3', 'active', '["support", "onboarding", "retention", "satisfaction"]', '{"response_time": 30}'),
    (gen_random_uuid(), 'MarketingAgent', 'specialist', 'gemini-pro', 'active', '["campaigns", "content", "seo", "analytics"]', '{"roi_target": 5}'),
    (gen_random_uuid(), 'SalesAgent', 'specialist', 'gpt-4', 'active', '["lead_generation", "qualification", "closing", "upsell"]', '{"quota": 100000}'),
    (gen_random_uuid(), 'CodeAgent', 'executor', 'gpt-4', 'active', '["write_code", "refactor", "optimize", "review"]', '{"languages": ["python", "typescript", "sql"]}'),
    (gen_random_uuid(), 'DatabaseAgent', 'executor', 'gpt-4', 'active', '["query", "optimize_query", "migrate", "backup"]', '{"db_type": "postgresql"}'),
    (gen_random_uuid(), 'InfrastructureAgent', 'executor', 'gpt-4', 'active', '["provision", "scale", "optimize_resources", "cost_control"]', '{"cloud": "multi"}'),
    (gen_random_uuid(), 'IntegrationAgent', 'executor', 'gpt-4', 'active', '["api_integration", "webhook", "sync", "transform"]', '{"protocols": ["rest", "graphql", "websocket"]}'),
    (gen_random_uuid(), 'AutomationAgent', 'executor', 'claude-3', 'active', '["workflow", "schedule", "trigger", "orchestrate"]', '{"engine": "langgraph"}'),
    (gen_random_uuid(), 'PerformanceAgent', 'analyzer', 'gpt-4', 'active', '["profile", "optimize", "cache", "load_balance"]', '{"target_latency": 200}'),
    (gen_random_uuid(), 'QualityAgent', 'guardian', 'claude-3', 'active', '["quality_check", "standards", "review", "improve"]', '{"threshold": 95}'),
    (gen_random_uuid(), 'DocumentationAgent', 'specialist', 'claude-3', 'active', '["document", "api_docs", "tutorials", "changelog"]', '{"format": "markdown"}'),
    (gen_random_uuid(), 'ResearchAgent', 'analyzer', 'gemini-pro', 'active', '["research", "analyze_competitors", "market_trends", "insights"]', '{"sources": 50}'),
    (gen_random_uuid(), 'PredictionAgent', 'analyzer', 'gpt-4', 'active', '["forecast", "predict", "simulate", "scenario_analysis"]', '{"accuracy_target": 85}'),
    (gen_random_uuid(), 'OptimizationAgent', 'analyzer', 'gpt-4', 'active', '["optimize_system", "resource_allocation", "cost_optimization"]', '{"efficiency_target": 90}'),
    (gen_random_uuid(), 'CommunicationAgent', 'specialist', 'claude-3', 'active', '["email", "slack", "notifications", "reports"]', '{"channels": ["email", "slack", "sms"]}'),
    (gen_random_uuid(), 'SchedulingAgent', 'executor', 'gpt-4', 'active', '["schedule", "calendar", "resource_planning", "availability"]', '{"timezone": "UTC"}'),
    (gen_random_uuid(), 'BillingAgent', 'executor', 'gpt-4', 'active', '["invoice", "payment_processing", "subscriptions", "dunning"]', '{"provider": "stripe"}'),
    (gen_random_uuid(), 'InventoryAgent', 'analyzer', 'gpt-4', 'active', '["track_inventory", "reorder", "forecast_demand", "optimize_stock"]', '{"min_stock": 100}'),
    (gen_random_uuid(), 'LogisticsAgent', 'executor', 'gpt-4', 'active', '["routing", "shipping", "tracking", "delivery"]', '{"carriers": ["ups", "fedex", "usps"]}')
ON CONFLICT (name) DO UPDATE 
SET status = 'active',
    model = EXCLUDED.model,
    capabilities = EXCLUDED.capabilities,
    config = EXCLUDED.config;

-- Create function to establish neural pathways properly
CREATE OR REPLACE FUNCTION establish_all_neural_pathways_v2()
RETURNS INTEGER AS $$
DECLARE
    pathway_count INTEGER := 0;
    source_agent RECORD;
    target_agent RECORD;
    new_pathway_id UUID;
BEGIN
    -- Create pathways between all agents
    FOR source_agent IN SELECT id, name, type FROM ai_agents WHERE status = 'active'
    LOOP
        FOR target_agent IN SELECT id, name, type FROM ai_agents WHERE status = 'active' AND id != source_agent.id
        LOOP
            -- Insert pathway
            INSERT INTO ai_neural_pathways_v2 (source_agent_id, target_agent_id, pathway_type, strength)
            VALUES (
                source_agent.id,
                target_agent.id,
                'bidirectional',
                CASE 
                    WHEN source_agent.type = 'orchestrator' OR target_agent.type = 'orchestrator' THEN 90
                    WHEN source_agent.type = target_agent.type THEN 70
                    ELSE 50
                END
            )
            ON CONFLICT (source_agent_id, target_agent_id) 
            DO UPDATE SET 
                strength = EXCLUDED.strength,
                last_activated = NOW()
            RETURNING id INTO new_pathway_id;
            
            IF new_pathway_id IS NOT NULL THEN
                pathway_count := pathway_count + 1;
            END IF;
        END LOOP;
    END LOOP;
    
    RETURN pathway_count;
END;
$$ LANGUAGE plpgsql;

-- Execute pathway establishment
SELECT establish_all_neural_pathways_v2();

-- Create initial AI Board session with proper fields
INSERT INTO ai_board_sessions (
    session_type,
    board_members,
    status,
    context,
    metadata,
    started_at
) VALUES (
    'system_initialization',
    ARRAY[]::UUID[], -- Empty array for board members
    'active',
    '{"purpose": "AI Brain Core Initialization", "mode": "autonomous"}',
    '{"brain_version": "3.0", "full_capabilities": true}',
    NOW()
) ON CONFLICT DO NOTHING;

-- Add ai_insights entry using correct columns
INSERT INTO ai_insights (
    type,
    title,
    description,
    confidence,
    impact,
    category,
    source,
    metadata
) VALUES (
    'system',
    'AI Brain Infrastructure Deployed',
    'Complete AI Brain with 34 agents and full neural pathway network established',
    95.0,
    'high',
    'infrastructure',
    'AI Brain Core',
    jsonb_build_object(
        'total_agents', (SELECT COUNT(*) FROM ai_agents WHERE status = 'active'),
        'total_pathways', (SELECT COUNT(*) FROM ai_neural_pathways_v2),
        'status', 'fully_operational',
        'timestamp', NOW()
    )
) ON CONFLICT DO NOTHING;

-- Update AUREA with extended capabilities
UPDATE ai_agents 
SET metadata = jsonb_build_object(
    'role', 'master_controller',
    'authority_level', 'maximum',
    'capabilities_extended', ARRAY[
        'autonomous_decision_making',
        'agent_orchestration', 
        'system_optimization',
        'self_healing',
        'predictive_analytics',
        'natural_language_understanding',
        'vision_processing',
        'continuous_learning'
    ],
    'initialized', true,
    'version', '3.0'
)
WHERE name = 'AUREA';

-- Create initial improvement cycle with proper columns
INSERT INTO ai_improvement_cycles (
    cycle_number,
    focus_area,
    baseline_metrics,
    target_metrics,
    participating_agents,
    started_at
) VALUES (
    1,
    'system_initialization',
    '{"agents": 7, "pathways": 0, "decisions": 0}',
    '{"agents": 34, "pathways": 1000, "decisions": 100}',
    (SELECT ARRAY_AGG(id) FROM ai_agents WHERE type = 'orchestrator'),
    NOW()
) ON CONFLICT DO NOTHING;

-- Verify complete deployment
SELECT 
    'AI BRAIN STATUS REPORT' as report,
    NOW() as timestamp;

SELECT 
    'Active Agents' as metric,
    COUNT(*) as value
FROM ai_agents 
WHERE status = 'active'
UNION ALL
SELECT 
    'Neural Pathways',
    COUNT(*)
FROM ai_neural_pathways_v2
UNION ALL
SELECT 
    'Active Sessions',
    COUNT(*)
FROM ai_board_sessions
WHERE status = 'active'
UNION ALL
SELECT 
    'Learning Cycles',
    COUNT(*)
FROM ai_improvement_cycles
WHERE completed_at IS NULL;

-- Show agent types distribution
SELECT 
    type as agent_type,
    COUNT(*) as count,
    STRING_AGG(name, ', ') as agents
FROM ai_agents
WHERE status = 'active'
GROUP BY type
ORDER BY count DESC;