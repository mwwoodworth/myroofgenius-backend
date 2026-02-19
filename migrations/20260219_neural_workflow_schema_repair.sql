-- 20260219_neural_workflow_schema_repair.sql
-- Purpose:
-- 1) Restore missing workflow analytics relations used by /api/v1/workflows/*
-- 2) Restore missing neural/board relations used by /api/v1/neural/*
-- 3) Add compatibility columns expected by legacy neural memory routes

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- Workflow analytics repair
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.agent_calls (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id uuid REFERENCES public.workflow_states(id) ON DELETE CASCADE,
    agent_name text NOT NULL,
    input jsonb,
    output jsonb,
    duration_ms integer,
    success boolean NOT NULL DEFAULT false,
    created_at timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_calls_workflow_id ON public.agent_calls(workflow_id);
CREATE INDEX IF NOT EXISTS idx_agent_calls_agent_name ON public.agent_calls(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_calls_created_at ON public.agent_calls(created_at DESC);

CREATE OR REPLACE VIEW public.agent_usage AS
SELECT
    ac.agent_name,
    COUNT(*)::bigint AS total_calls,
    COUNT(*) FILTER (WHERE ac.success)::bigint AS successful_calls,
    COUNT(*) FILTER (WHERE NOT ac.success)::bigint AS failed_calls,
    CASE
        WHEN COUNT(*) = 0 THEN 0::numeric
        ELSE ROUND((COUNT(*) FILTER (WHERE ac.success)::numeric * 100.0) / COUNT(*)::numeric, 2)
    END AS success_rate,
    ROUND(AVG(ac.duration_ms)::numeric, 2) AS avg_duration_ms,
    MAX(ac.created_at) AS last_used_at
FROM public.agent_calls ac
GROUP BY ac.agent_name
ORDER BY total_calls DESC;

-- ============================================================================
-- Neural network table repair
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.ai_neurons (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    neuron_type text NOT NULL,
    layer_id integer,
    activation_function text NOT NULL DEFAULT 'sigmoid',
    threshold double precision NOT NULL DEFAULT 0.5,
    current_value double precision NOT NULL DEFAULT 0.0,
    metadata jsonb,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_at timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_neurons_is_active ON public.ai_neurons(is_active);
CREATE INDEX IF NOT EXISTS idx_ai_neurons_layer_id ON public.ai_neurons(layer_id);
CREATE INDEX IF NOT EXISTS idx_ai_neurons_type ON public.ai_neurons(neuron_type);

CREATE TABLE IF NOT EXISTS public.ai_synapses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_neuron_id uuid NOT NULL REFERENCES public.ai_neurons(id) ON DELETE CASCADE,
    target_neuron_id uuid NOT NULL REFERENCES public.ai_neurons(id) ON DELETE CASCADE,
    weight double precision NOT NULL DEFAULT 0.5,
    synapse_type text NOT NULL DEFAULT 'excitatory',
    learning_rate double precision NOT NULL DEFAULT 0.1,
    signal_count integer NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_at timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_synapses_is_active ON public.ai_synapses(is_active);
CREATE INDEX IF NOT EXISTS idx_ai_synapses_source ON public.ai_synapses(source_neuron_id);
CREATE INDEX IF NOT EXISTS idx_ai_synapses_target ON public.ai_synapses(target_neuron_id);

CREATE TABLE IF NOT EXISTS public.ai_neural_pathways (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    pathway_name text,
    neuron_sequence jsonb,
    activation_pattern jsonb,
    total_strength double precision NOT NULL DEFAULT 0.0,
    source_agent_id uuid REFERENCES public.ai_agents(id) ON DELETE SET NULL,
    target_agent_id uuid REFERENCES public.ai_agents(id) ON DELETE SET NULL,
    pathway_type text,
    strength double precision,
    created_at timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_neural_pathways_created_at ON public.ai_neural_pathways(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_neural_pathways_name ON public.ai_neural_pathways(pathway_name);
CREATE INDEX IF NOT EXISTS idx_ai_neural_pathways_agents ON public.ai_neural_pathways(source_agent_id, target_agent_id);

-- ============================================================================
-- AI board + decision table repair
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.ai_board_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_name text,
    participants jsonb,
    decision_topic text,
    voting_method text NOT NULL DEFAULT 'consensus',
    status text NOT NULL DEFAULT 'active',
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    timeout_at timestamp without time zone,
    -- Compatibility columns used by other legacy brain modules
    session_id text,
    started_at timestamp without time zone,
    context jsonb,
    metadata jsonb
);

CREATE INDEX IF NOT EXISTS idx_ai_board_sessions_status ON public.ai_board_sessions(status);
CREATE INDEX IF NOT EXISTS idx_ai_board_sessions_created_at ON public.ai_board_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_board_sessions_session_id ON public.ai_board_sessions(session_id);

CREATE TABLE IF NOT EXISTS public.ai_board_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id text NOT NULL,
    agent_id text,
    action_type text NOT NULL,
    action_data jsonb,
    created_at timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_board_logs_session_id ON public.ai_board_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_board_logs_created_at ON public.ai_board_logs(created_at DESC);

CREATE TABLE IF NOT EXISTS public.ai_consensus_decisions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id text NOT NULL,
    decision_data jsonb NOT NULL DEFAULT '{}'::jsonb,
    confidence_score double precision NOT NULL DEFAULT 0.0,
    supporting_evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
    status text NOT NULL DEFAULT 'finalized',
    created_at timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_consensus_decisions_session_id ON public.ai_consensus_decisions(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_consensus_decisions_created_at ON public.ai_consensus_decisions(created_at DESC);

-- ============================================================================
-- Neural memory compatibility repair
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.ai_memory_clusters (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_name text NOT NULL,
    memory_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    clustering_algorithm text,
    cluster_parameters jsonb,
    cluster_centers jsonb,
    created_at timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_memory_clusters_created_at ON public.ai_memory_clusters(created_at DESC);

CREATE TABLE IF NOT EXISTS public.ai_patterns (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type text NOT NULL,
    pattern_data jsonb NOT NULL DEFAULT '{}'::jsonb,
    confidence_score double precision NOT NULL DEFAULT 0.0,
    associated_memories jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_patterns_created_at ON public.ai_patterns(created_at DESC);

CREATE TABLE IF NOT EXISTS public.ai_memory_relationships (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_memory_id text,
    target_memory_id text,
    relationship_type text NOT NULL DEFAULT 'association',
    strength double precision NOT NULL DEFAULT 1.0,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    UNIQUE (source_memory_id, target_memory_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_ai_memory_relationships_source ON public.ai_memory_relationships(source_memory_id);
CREATE INDEX IF NOT EXISTS idx_ai_memory_relationships_target ON public.ai_memory_relationships(target_memory_id);

ALTER TABLE public.ai_memories
    ADD COLUMN IF NOT EXISTS importance_score double precision,
    ADD COLUMN IF NOT EXISTS associations text,
    ADD COLUMN IF NOT EXISTS content_embedding text;

UPDATE public.ai_memories
SET importance_score = COALESCE(importance::double precision, 0.5)
WHERE importance_score IS NULL;

UPDATE public.ai_memories
SET associations = COALESCE(to_json(related_memories)::text, '[]')
WHERE associations IS NULL;

UPDATE public.ai_memories
SET content_embedding = COALESCE(to_json(vector_data)::text, '[]')
WHERE content_embedding IS NULL;

-- ============================================================================
-- Internal service role grants/policies (prevents backend/agent RLS regressions)
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    public.agent_calls,
    public.ai_neurons,
    public.ai_synapses,
    public.ai_neural_pathways,
    public.ai_board_sessions,
    public.ai_board_logs,
    public.ai_consensus_decisions,
    public.ai_memory_clusters,
    public.ai_patterns,
    public.ai_memory_relationships
TO app_backend_role, brainops_backend;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    public.ai_autonomous_tasks
TO app_agent_role, app_backend_role, brainops_backend;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'ai_memories'
          AND policyname = 'backend_service_bypass_ai_memories'
    ) THEN
        EXECUTE $sql$
            CREATE POLICY backend_service_bypass_ai_memories
            ON public.ai_memories
            FOR ALL
            TO app_backend_role, brainops_backend
            USING (true)
            WITH CHECK (true)
        $sql$;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'ai_autonomous_tasks'
          AND policyname = 'backend_service_bypass_ai_autonomous_tasks'
    ) THEN
        EXECUTE $sql$
            CREATE POLICY backend_service_bypass_ai_autonomous_tasks
            ON public.ai_autonomous_tasks
            FOR ALL
            TO app_backend_role, app_agent_role, brainops_backend
            USING (true)
            WITH CHECK (true)
        $sql$;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'neural_pathways'
          AND policyname = 'brainops_backend_all_neural_pathways'
    ) THEN
        EXECUTE $sql$
            CREATE POLICY brainops_backend_all_neural_pathways
            ON public.neural_pathways
            FOR ALL
            TO brainops_backend
            USING (true)
            WITH CHECK (true)
        $sql$;
    END IF;
END $$;

COMMIT;
