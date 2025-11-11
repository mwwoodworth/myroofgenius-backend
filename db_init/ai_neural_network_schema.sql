-- ============================================================================
-- AI NEURAL NETWORK OPERATING SYSTEM - DATABASE SCHEMA
-- ============================================================================
-- This creates an intricate web of interconnected AI agents functioning as
-- a comprehensive intelligent operating system with persistent memory
-- ============================================================================

-- Drop existing tables if they exist (for clean installation)
DROP TABLE IF EXISTS ai_agent_connections CASCADE;
DROP TABLE IF EXISTS ai_neural_pathways CASCADE;
DROP TABLE IF EXISTS ai_synapses CASCADE;
DROP TABLE IF EXISTS ai_neurons CASCADE;
DROP TABLE IF EXISTS ai_agents CASCADE;
DROP TABLE IF EXISTS ai_memory_clusters CASCADE;
DROP TABLE IF EXISTS ai_decision_logs CASCADE;
DROP TABLE IF EXISTS ai_learning_patterns CASCADE;
DROP TABLE IF EXISTS ai_consensus_decisions CASCADE;
DROP TABLE IF EXISTS brainlink_events CASCADE;
DROP TABLE IF EXISTS ai_board_sessions CASCADE;
DROP TABLE IF EXISTS ai_improvement_cycles CASCADE;

-- ============================================================================
-- CORE AI AGENTS TABLE - The "Neurons" of our system
-- ============================================================================
CREATE TABLE ai_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL, -- 'orchestrator', 'specialist', 'validator', 'learner'
    model VARCHAR(50) NOT NULL, -- 'claude-3', 'gpt-4', 'gemini-pro', 'llama', etc.
    capabilities JSONB NOT NULL DEFAULT '[]',
    specializations TEXT[],
    confidence_score DECIMAL(3,2) DEFAULT 0.80,
    energy_level INTEGER DEFAULT 100, -- 0-100, affects decision making
    experience_points INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'learning', 'resting', 'failed'
    config JSONB DEFAULT '{}',
    last_activation TIMESTAMP WITH TIME ZONE,
    total_activations INTEGER DEFAULT 0,
    success_rate DECIMAL(3,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1),
    CONSTRAINT valid_energy CHECK (energy_level >= 0 AND energy_level <= 100)
);

-- ============================================================================
-- AI NEURONS - Individual processing units within agents
-- ============================================================================
CREATE TABLE ai_neurons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES ai_agents(id) ON DELETE CASCADE,
    neuron_type VARCHAR(50) NOT NULL, -- 'input', 'hidden', 'output', 'memory'
    layer INTEGER NOT NULL, -- 0 for input, 1+ for hidden, -1 for output
    activation_function VARCHAR(50) DEFAULT 'relu', -- 'relu', 'sigmoid', 'tanh'
    weight DECIMAL(10,6) DEFAULT 1.0,
    bias DECIMAL(10,6) DEFAULT 0.0,
    activation_threshold DECIMAL(10,6) DEFAULT 0.5,
    current_value DECIMAL(10,6) DEFAULT 0.0,
    last_fired TIMESTAMP WITH TIME ZONE,
    fire_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AI SYNAPSES - Connections between neurons
-- ============================================================================
CREATE TABLE ai_synapses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_neuron_id UUID NOT NULL REFERENCES ai_neurons(id) ON DELETE CASCADE,
    to_neuron_id UUID NOT NULL REFERENCES ai_neurons(id) ON DELETE CASCADE,
    connection_strength DECIMAL(10,6) DEFAULT 1.0,
    plasticity DECIMAL(3,2) DEFAULT 0.5, -- How easily the connection changes
    transmission_speed INTEGER DEFAULT 100, -- milliseconds
    neurotransmitter_type VARCHAR(50) DEFAULT 'excitatory', -- 'excitatory', 'inhibitory', 'modulatory'
    last_transmission TIMESTAMP WITH TIME ZONE,
    transmission_count INTEGER DEFAULT 0,
    learning_rate DECIMAL(10,6) DEFAULT 0.01,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_synapse UNIQUE(from_neuron_id, to_neuron_id),
    CONSTRAINT valid_strength CHECK (connection_strength >= -10 AND connection_strength <= 10)
);

-- ============================================================================
-- AI NEURAL PATHWAYS - Established routes for information flow
-- ============================================================================
CREATE TABLE ai_neural_pathways (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    pathway_type VARCHAR(50) NOT NULL, -- 'decision', 'memory', 'learning', 'reflex'
    neurons UUID[] NOT NULL, -- Ordered array of neuron IDs
    activation_count INTEGER DEFAULT 0,
    average_latency INTEGER, -- milliseconds
    reliability_score DECIMAL(3,2) DEFAULT 1.0,
    is_primary BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- AI AGENT CONNECTIONS - Direct agent-to-agent relationships
-- ============================================================================
CREATE TABLE ai_agent_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_agent_id UUID NOT NULL REFERENCES ai_agents(id) ON DELETE CASCADE,
    to_agent_id UUID NOT NULL REFERENCES ai_agents(id) ON DELETE CASCADE,
    connection_type VARCHAR(50) NOT NULL, -- 'supervisor', 'peer', 'subordinate', 'consultant'
    trust_level DECIMAL(3,2) DEFAULT 0.50,
    communication_protocol VARCHAR(50) DEFAULT 'async', -- 'sync', 'async', 'broadcast'
    shared_memory_access BOOLEAN DEFAULT false,
    interaction_count INTEGER DEFAULT 0,
    last_interaction TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_connection UNIQUE(from_agent_id, to_agent_id),
    CONSTRAINT valid_trust CHECK (trust_level >= 0 AND trust_level <= 1)
);

-- ============================================================================
-- BRAINLINK EVENTS - Event-driven communication system
-- ============================================================================
CREATE TABLE brainlink_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    channel VARCHAR(100) NOT NULL, -- 'task_delegation', 'context_sharing', 'error_recovery', 'consensus'
    sender_agent_id UUID REFERENCES ai_agents(id),
    recipient_agent_ids UUID[],
    priority INTEGER DEFAULT 5, -- 1 (highest) to 10 (lowest)
    payload JSONB NOT NULL,
    require_consensus BOOLEAN DEFAULT false,
    consensus_threshold DECIMAL(3,2) DEFAULT 0.66,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    responses JSONB DEFAULT '[]',
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    ttl_seconds INTEGER DEFAULT 3600, -- Time to live
    CONSTRAINT valid_priority CHECK (priority >= 1 AND priority <= 10)
);

-- ============================================================================
-- AI MEMORY CLUSTERS - Grouped memories for context
-- ============================================================================
CREATE TABLE ai_memory_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_name VARCHAR(255) NOT NULL,
    cluster_type VARCHAR(50) NOT NULL, -- 'episodic', 'semantic', 'procedural', 'working'
    agent_ids UUID[], -- Agents that can access this cluster
    memories JSONB NOT NULL DEFAULT '[]',
    vector_embedding vector(1536), -- For similarity search
    importance_score DECIMAL(3,2) DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    consolidation_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    last_consolidated TIMESTAMP WITH TIME ZONE,
    retention_priority INTEGER DEFAULT 5, -- 1-10, higher = keep longer
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_importance CHECK (importance_score >= 0 AND importance_score <= 1)
);

-- ============================================================================
-- AI DECISION LOGS - Track all decisions for learning
-- ============================================================================
CREATE TABLE ai_decision_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    agent_id UUID NOT NULL REFERENCES ai_agents(id),
    decision_type VARCHAR(100) NOT NULL,
    context JSONB NOT NULL,
    options_considered JSONB NOT NULL,
    chosen_option JSONB NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    reasoning TEXT,
    outcome VARCHAR(50), -- 'success', 'failure', 'partial', 'unknown'
    feedback_score DECIMAL(3,2), -- Human or system feedback
    contributing_agents UUID[], -- Other agents that influenced decision
    neural_pathway_id UUID REFERENCES ai_neural_pathways(id),
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    evaluated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1),
    CONSTRAINT valid_feedback CHECK (feedback_score IS NULL OR (feedback_score >= 0 AND feedback_score <= 1))
);

-- ============================================================================
-- AI LEARNING PATTERNS - Identified patterns for improvement
-- ============================================================================
CREATE TABLE ai_learning_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL, -- 'success', 'failure', 'optimization', 'innovation'
    discovered_by_agent_id UUID REFERENCES ai_agents(id),
    pattern_data JSONB NOT NULL,
    occurrence_count INTEGER DEFAULT 1,
    success_rate DECIMAL(3,2),
    applicability_score DECIMAL(3,2) DEFAULT 0.5,
    shared_with_agents UUID[] DEFAULT '{}',
    implementation_status VARCHAR(20) DEFAULT 'discovered', -- 'discovered', 'testing', 'validated', 'deployed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP WITH TIME ZONE,
    deployed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_success_rate CHECK (success_rate IS NULL OR (success_rate >= 0 AND success_rate <= 1))
);

-- ============================================================================
-- AI CONSENSUS DECISIONS - Multi-agent voting results
-- ============================================================================
CREATE TABLE ai_consensus_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_topic VARCHAR(255) NOT NULL,
    initiator_agent_id UUID REFERENCES ai_agents(id),
    participating_agents UUID[] NOT NULL,
    voting_data JSONB NOT NULL, -- {agent_id: {vote, confidence, reasoning}}
    consensus_type VARCHAR(50) NOT NULL, -- 'unanimous', 'majority', 'weighted', 'quorum'
    threshold_required DECIMAL(3,2) NOT NULL,
    threshold_achieved DECIMAL(3,2),
    final_decision JSONB,
    dissenting_opinions JSONB DEFAULT '[]',
    execution_plan JSONB,
    status VARCHAR(20) DEFAULT 'voting', -- 'voting', 'decided', 'executing', 'completed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    decided_at TIMESTAMP WITH TIME ZONE,
    executed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_threshold CHECK (threshold_required >= 0 AND threshold_required <= 1)
);

-- ============================================================================
-- AI BOARD SESSIONS - High-level governance meetings
-- ============================================================================
CREATE TABLE ai_board_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_type VARCHAR(50) NOT NULL, -- 'strategic', 'operational', 'emergency', 'review'
    board_members UUID[] NOT NULL, -- Agent IDs serving as board members
    agenda JSONB NOT NULL,
    decisions_made JSONB DEFAULT '[]',
    action_items JSONB DEFAULT '[]',
    metrics_reviewed JSONB DEFAULT '{}',
    performance_score DECIMAL(3,2),
    next_session_scheduled TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'scheduled', -- 'scheduled', 'in_progress', 'completed', 'cancelled'
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_performance CHECK (performance_score IS NULL OR (performance_score >= 0 AND performance_score <= 1))
);

-- ============================================================================
-- AI IMPROVEMENT CYCLES - Self-improvement tracking
-- ============================================================================
CREATE TABLE ai_improvement_cycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_number INTEGER NOT NULL,
    focus_area VARCHAR(100) NOT NULL,
    baseline_metrics JSONB NOT NULL,
    target_metrics JSONB NOT NULL,
    achieved_metrics JSONB,
    improvements_implemented JSONB DEFAULT '[]',
    participating_agents UUID[] NOT NULL,
    success_rate DECIMAL(3,2),
    lessons_learned TEXT[],
    next_cycle_recommendations JSONB,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_success CHECK (success_rate IS NULL OR (success_rate >= 0 AND success_rate <= 1))
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================
CREATE INDEX idx_agents_status ON ai_agents(status);
CREATE INDEX idx_agents_type ON ai_agents(type);
CREATE INDEX idx_neurons_agent ON ai_neurons(agent_id);
CREATE INDEX idx_neurons_layer ON ai_neurons(layer);
CREATE INDEX idx_synapses_from ON ai_synapses(from_neuron_id);
CREATE INDEX idx_synapses_to ON ai_synapses(to_neuron_id);
CREATE INDEX idx_pathways_type ON ai_neural_pathways(pathway_type);
CREATE INDEX idx_connections_from ON ai_agent_connections(from_agent_id);
CREATE INDEX idx_connections_to ON ai_agent_connections(to_agent_id);
CREATE INDEX idx_events_status ON brainlink_events(status);
CREATE INDEX idx_events_channel ON brainlink_events(channel);
CREATE INDEX idx_events_created ON brainlink_events(created_at DESC);
CREATE INDEX idx_memory_clusters_type ON ai_memory_clusters(cluster_type);
CREATE INDEX idx_memory_clusters_vector ON ai_memory_clusters USING ivfflat (vector_embedding vector_cosine_ops);
CREATE INDEX idx_decisions_agent ON ai_decision_logs(agent_id);
CREATE INDEX idx_decisions_session ON ai_decision_logs(session_id);
CREATE INDEX idx_decisions_created ON ai_decision_logs(created_at DESC);
CREATE INDEX idx_patterns_type ON ai_learning_patterns(pattern_type);
CREATE INDEX idx_consensus_status ON ai_consensus_decisions(status);
CREATE INDEX idx_board_status ON ai_board_sessions(status);
CREATE INDEX idx_improvement_cycle ON ai_improvement_cycles(cycle_number);

-- ============================================================================
-- INITIAL SEED DATA - Core AI Agents
-- ============================================================================
INSERT INTO ai_agents (name, type, model, capabilities, specializations, confidence_score) VALUES
-- Master Orchestrators
('AUREA', 'orchestrator', 'claude-3-opus', 
 '["natural_language", "vision", "reasoning", "planning", "execution"]'::jsonb,
 ARRAY['executive_decisions', 'strategic_planning', 'system_orchestration'],
 0.95),

('AIBoard', 'orchestrator', 'gpt-4', 
 '["governance", "consensus", "monitoring", "reporting"]'::jsonb,
 ARRAY['board_governance', 'performance_review', 'compliance'],
 0.90),

-- Specialist Agents
('Claude_Analyst', 'specialist', 'claude-3-sonnet',
 '["analysis", "research", "documentation"]'::jsonb,
 ARRAY['data_analysis', 'pattern_recognition', 'report_generation'],
 0.88),

('Gemini_Creative', 'specialist', 'gemini-pro',
 '["creative", "multimodal", "generation"]'::jsonb,
 ARRAY['content_creation', 'image_analysis', 'marketing'],
 0.85),

('GPT_Engineer', 'specialist', 'gpt-4-turbo',
 '["coding", "architecture", "optimization"]'::jsonb,
 ARRAY['software_development', 'system_design', 'debugging'],
 0.87),

-- Validators
('Validator_Prime', 'validator', 'claude-3-haiku',
 '["validation", "testing", "quality_assurance"]'::jsonb,
 ARRAY['accuracy_checking', 'fact_verification', 'compliance_validation'],
 0.92),

-- Learners
('Learning_Core', 'learner', 'gpt-3.5-turbo',
 '["pattern_learning", "adaptation", "optimization"]'::jsonb,
 ARRAY['ml_optimization', 'pattern_discovery', 'self_improvement'],
 0.80);

-- ============================================================================
-- FUNCTIONS FOR NEURAL OPERATIONS
-- ============================================================================

-- Function to fire a neuron and propagate signals
CREATE OR REPLACE FUNCTION fire_neuron(neuron_id UUID)
RETURNS TABLE(affected_neurons UUID[], pathway_activated UUID) AS $$
DECLARE
    v_synapses RECORD;
    v_affected UUID[] := '{}';
    v_pathway UUID;
BEGIN
    -- Update neuron fire count and timestamp
    UPDATE ai_neurons 
    SET last_fired = CURRENT_TIMESTAMP,
        fire_count = fire_count + 1
    WHERE id = neuron_id;
    
    -- Propagate to connected neurons
    FOR v_synapses IN 
        SELECT s.*, n.activation_threshold, n.current_value
        FROM ai_synapses s
        JOIN ai_neurons n ON n.id = s.to_neuron_id
        WHERE s.from_neuron_id = neuron_id
    LOOP
        -- Apply connection strength to signal
        UPDATE ai_neurons
        SET current_value = current_value + v_synapses.connection_strength
        WHERE id = v_synapses.to_neuron_id;
        
        v_affected := array_append(v_affected, v_synapses.to_neuron_id);
        
        -- Update synapse statistics
        UPDATE ai_synapses
        SET last_transmission = CURRENT_TIMESTAMP,
            transmission_count = transmission_count + 1
        WHERE id = v_synapses.id;
    END LOOP;
    
    -- Check if this activated a pathway
    SELECT id INTO v_pathway
    FROM ai_neural_pathways
    WHERE neuron_id = ANY(neurons)
    ORDER BY reliability_score DESC
    LIMIT 1;
    
    IF v_pathway IS NOT NULL THEN
        UPDATE ai_neural_pathways
        SET activation_count = activation_count + 1,
            last_used = CURRENT_TIMESTAMP
        WHERE id = v_pathway;
    END IF;
    
    RETURN QUERY SELECT v_affected, v_pathway;
END;
$$ LANGUAGE plpgsql;

-- Function to process BrainLink events
CREATE OR REPLACE FUNCTION process_brainlink_event(event_id UUID)
RETURNS JSONB AS $$
DECLARE
    v_event RECORD;
    v_responses JSONB := '[]'::jsonb;
    v_agent_response JSONB;
    v_consensus_reached BOOLEAN := false;
    v_final_result JSONB;
BEGIN
    -- Get event details
    SELECT * INTO v_event FROM brainlink_events WHERE id = event_id;
    
    IF v_event.status != 'pending' THEN
        RETURN jsonb_build_object('error', 'Event already processed');
    END IF;
    
    -- Update status to processing
    UPDATE brainlink_events 
    SET status = 'processing', 
        processed_at = CURRENT_TIMESTAMP
    WHERE id = event_id;
    
    -- If consensus required, create consensus decision
    IF v_event.require_consensus THEN
        INSERT INTO ai_consensus_decisions (
            decision_topic,
            initiator_agent_id,
            participating_agents,
            consensus_type,
            threshold_required,
            voting_data
        ) VALUES (
            v_event.event_type,
            v_event.sender_agent_id,
            v_event.recipient_agent_ids,
            'weighted',
            v_event.consensus_threshold,
            '{}'::jsonb
        );
    END IF;
    
    -- Process event based on channel
    CASE v_event.channel
        WHEN 'task_delegation' THEN
            -- Add to job queue for processing
            INSERT INTO job_queue (job_type, payload, priority)
            VALUES ('ai_task', v_event.payload, v_event.priority);
            
        WHEN 'context_sharing' THEN
            -- Store in memory cluster
            INSERT INTO ai_memory_clusters (
                cluster_name,
                cluster_type,
                agent_ids,
                memories
            ) VALUES (
                'shared_context_' || v_event.id,
                'working',
                v_event.recipient_agent_ids,
                jsonb_build_array(v_event.payload)
            );
            
        WHEN 'error_recovery' THEN
            -- Trigger recovery workflow
            v_final_result := jsonb_build_object(
                'recovery_initiated', true,
                'timestamp', CURRENT_TIMESTAMP
            );
            
        WHEN 'consensus' THEN
            -- Wait for voting to complete
            v_consensus_reached := true;
            
        ELSE
            v_final_result := jsonb_build_object('status', 'processed');
    END CASE;
    
    -- Update event with results
    UPDATE brainlink_events
    SET status = 'completed',
        completed_at = CURRENT_TIMESTAMP,
        result = v_final_result,
        responses = v_responses
    WHERE id = event_id;
    
    RETURN v_final_result;
END;
$$ LANGUAGE plpgsql;

-- Function to strengthen neural pathways based on success
CREATE OR REPLACE FUNCTION strengthen_pathway(pathway_id UUID, success BOOLEAN)
RETURNS void AS $$
DECLARE
    v_adjustment DECIMAL(10,6);
BEGIN
    -- Calculate adjustment based on success
    v_adjustment := CASE WHEN success THEN 0.1 ELSE -0.05 END;
    
    -- Update pathway reliability
    UPDATE ai_neural_pathways
    SET reliability_score = LEAST(1.0, GREATEST(0.0, reliability_score + v_adjustment))
    WHERE id = pathway_id;
    
    -- Strengthen/weaken synapses in the pathway
    UPDATE ai_synapses s
    SET connection_strength = LEAST(10.0, GREATEST(-10.0, 
        connection_strength + (v_adjustment * s.plasticity)))
    FROM ai_neural_pathways p
    WHERE p.id = pathway_id
    AND s.from_neuron_id = ANY(p.neurons)
    AND s.to_neuron_id = ANY(p.neurons);
END;
$$ LANGUAGE plpgsql;

-- Function to consolidate memories
CREATE OR REPLACE FUNCTION consolidate_memories()
RETURNS void AS $$
BEGIN
    -- Merge similar memory clusters
    WITH similar_clusters AS (
        SELECT 
            c1.id as cluster1_id,
            c2.id as cluster2_id,
            1 - (c1.vector_embedding <=> c2.vector_embedding) as similarity
        FROM ai_memory_clusters c1
        JOIN ai_memory_clusters c2 ON c1.id < c2.id
        WHERE c1.cluster_type = c2.cluster_type
        AND 1 - (c1.vector_embedding <=> c2.vector_embedding) > 0.85
    )
    UPDATE ai_memory_clusters c
    SET memories = c.memories || c2.memories,
        consolidation_count = c.consolidation_count + 1,
        last_consolidated = CURRENT_TIMESTAMP
    FROM similar_clusters sc
    JOIN ai_memory_clusters c2 ON c2.id = sc.cluster2_id
    WHERE c.id = sc.cluster1_id;
    
    -- Delete consolidated clusters
    DELETE FROM ai_memory_clusters
    WHERE id IN (
        SELECT cluster2_id 
        FROM (
            SELECT c2.id as cluster2_id
            FROM ai_memory_clusters c1
            JOIN ai_memory_clusters c2 ON c1.id < c2.id
            WHERE c1.cluster_type = c2.cluster_type
            AND 1 - (c1.vector_embedding <=> c2.vector_embedding) > 0.85
        ) t
    );
    
    -- Clean up old, low-importance memories
    DELETE FROM ai_memory_clusters
    WHERE importance_score < 0.3
    AND last_accessed < CURRENT_TIMESTAMP - INTERVAL '30 days'
    AND retention_priority < 5;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS FOR AUTOMATION
-- ============================================================================

-- Auto-update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_agents_timestamp
    BEFORE UPDATE ON ai_agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Auto-process BrainLink events
CREATE OR REPLACE FUNCTION auto_process_event()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.priority <= 3 THEN
        -- High priority events processed immediately
        PERFORM process_brainlink_event(NEW.id);
    ELSE
        -- Lower priority added to queue
        INSERT INTO job_queue (job_type, payload, priority)
        VALUES ('brainlink_event', jsonb_build_object('event_id', NEW.id), NEW.priority);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER process_new_event
    AFTER INSERT ON brainlink_events
    FOR EACH ROW EXECUTE FUNCTION auto_process_event();

-- ============================================================================
-- PERMISSIONS
-- ============================================================================
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================
COMMENT ON TABLE ai_agents IS 'Core AI agents that form the neural network of the system';
COMMENT ON TABLE ai_neurons IS 'Individual processing units within each AI agent';
COMMENT ON TABLE ai_synapses IS 'Connections between neurons enabling information flow';
COMMENT ON TABLE ai_neural_pathways IS 'Established routes for efficient information processing';
COMMENT ON TABLE brainlink_events IS 'Event-driven communication system for agent coordination';
COMMENT ON TABLE ai_memory_clusters IS 'Grouped memories for context and learning';
COMMENT ON TABLE ai_decision_logs IS 'Complete history of all AI decisions for learning';
COMMENT ON TABLE ai_consensus_decisions IS 'Multi-agent voting and consensus records';
COMMENT ON TABLE ai_board_sessions IS 'High-level governance and strategic planning sessions';