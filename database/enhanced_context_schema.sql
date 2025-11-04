-- BrainOps Enhanced Context System Schema
-- Uses EXISTING pgvector extension (v0.8.0) - NO ADDITIONAL COST
-- Deployed: 2025-10-18

-- Enable extensions (already available in Supabase)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- ============================================================================
-- ENHANCED CONTEXT STORAGE WITH VECTOR EMBEDDINGS
-- ============================================================================

-- Vector embeddings for semantic search (uses OpenAI ada-002: 1536 dimensions)
CREATE TABLE IF NOT EXISTS context_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  embedding vector(1536),  -- OpenAI embedding dimension
  context_type VARCHAR(50) NOT NULL CHECK (context_type IN (
    'code', 'knowledge', 'interaction', 'decision', 'bug_fix', 'deployment'
  )),
  metadata JSONB DEFAULT '{}',
  session_id UUID REFERENCES claude_sessions(id) ON DELETE CASCADE,
  relevance_score FLOAT DEFAULT 1.0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Optimized index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON context_embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Additional indexes for filtering
CREATE INDEX IF NOT EXISTS idx_embeddings_type ON context_embeddings(context_type);
CREATE INDEX IF NOT EXISTS idx_embeddings_session ON context_embeddings(session_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_created ON context_embeddings(created_at DESC);

-- Full-text search support
CREATE INDEX IF NOT EXISTS idx_embeddings_content_fts ON context_embeddings
  USING gin(to_tsvector('english', content));

-- ============================================================================
-- KNOWLEDGE GRAPH FOR INTERCONNECTED LEARNINGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_relationships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_knowledge_id UUID REFERENCES system_knowledge(id) ON DELETE CASCADE,
  target_knowledge_id UUID REFERENCES system_knowledge(id) ON DELETE CASCADE,
  relationship_type VARCHAR(50) NOT NULL CHECK (relationship_type IN (
    'depends_on', 'conflicts_with', 'enhances', 'replaces',
    'requires', 'inspired_by', 'related_to'
  )),
  strength FLOAT DEFAULT 1.0 CHECK (strength >= 0 AND strength <= 1),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  verified_at TIMESTAMP WITH TIME ZONE,
  UNIQUE(source_knowledge_id, target_knowledge_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_rel_source ON knowledge_relationships(source_knowledge_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_rel_target ON knowledge_relationships(target_knowledge_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_rel_type ON knowledge_relationships(relationship_type);

-- ============================================================================
-- DECISION HISTORY FOR TRACKING IMPORTANT CHOICES
-- ============================================================================

CREATE TABLE IF NOT EXISTS decision_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES claude_sessions(id) ON DELETE CASCADE,
  decision_type VARCHAR(100) NOT NULL,
  context TEXT NOT NULL,
  chosen_option TEXT NOT NULL,
  alternatives JSONB DEFAULT '[]',
  reasoning TEXT,
  outcome TEXT,
  success BOOLEAN,
  impact_level VARCHAR(20) CHECK (impact_level IN ('low', 'medium', 'high', 'critical')),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  evaluated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_decision_session ON decision_history(session_id);
CREATE INDEX IF NOT EXISTS idx_decision_type ON decision_history(decision_type);
CREATE INDEX IF NOT EXISTS idx_decision_success ON decision_history(success);
CREATE INDEX IF NOT EXISTS idx_decision_impact ON decision_history(impact_level);

-- ============================================================================
-- LEARNING PATTERNS FOR CROSS-SESSION INTELLIGENCE
-- ============================================================================

CREATE TABLE IF NOT EXISTS learning_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pattern_name VARCHAR(200) NOT NULL UNIQUE,
  pattern_type VARCHAR(50) NOT NULL CHECK (pattern_type IN (
    'bug_fix', 'optimization', 'refactoring', 'deployment',
    'testing', 'security', 'performance'
  )),
  trigger_conditions JSONB NOT NULL,  -- What triggers this pattern
  recommended_actions JSONB NOT NULL,  -- What to do when triggered
  success_rate FLOAT DEFAULT 0.0,
  times_applied INTEGER DEFAULT 0,
  average_duration_ms INTEGER,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_applied TIMESTAMP WITH TIME ZONE,
  last_success TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_patterns_type ON learning_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_success ON learning_patterns(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_usage ON learning_patterns(times_applied DESC);

-- ============================================================================
-- PATTERN APPLICATIONS (Track when patterns are used)
-- ============================================================================

CREATE TABLE IF NOT EXISTS pattern_applications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pattern_id UUID REFERENCES learning_patterns(id) ON DELETE CASCADE,
  session_id UUID REFERENCES claude_sessions(id) ON DELETE CASCADE,
  context TEXT,
  success BOOLEAN,
  duration_ms INTEGER,
  outcome TEXT,
  metadata JSONB DEFAULT '{}',
  applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pattern_apps_pattern ON pattern_applications(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_apps_session ON pattern_applications(session_id);
CREATE INDEX IF NOT EXISTS idx_pattern_apps_success ON pattern_applications(success);

-- ============================================================================
-- CODE CHANGE TRACKING (Enhanced)
-- ============================================================================

CREATE TABLE IF NOT EXISTS code_changes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES claude_sessions(id) ON DELETE CASCADE,
  file_path TEXT NOT NULL,
  change_type VARCHAR(20) CHECK (change_type IN ('create', 'modify', 'delete', 'rename')),
  lines_added INTEGER DEFAULT 0,
  lines_removed INTEGER DEFAULT 0,
  diff_summary TEXT,
  reason TEXT,
  risk_assessment VARCHAR(20) CHECK (risk_assessment IN ('low', 'medium', 'high', 'critical')),
  tested BOOLEAN DEFAULT FALSE,
  deployed BOOLEAN DEFAULT FALSE,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_code_changes_session ON code_changes(session_id);
CREATE INDEX IF NOT EXISTS idx_code_changes_file ON code_changes(file_path);
CREATE INDEX IF NOT EXISTS idx_code_changes_risk ON code_changes(risk_assessment);

-- ============================================================================
-- SESSION SUMMARY (Auto-generated session insights)
-- ============================================================================

CREATE TABLE IF NOT EXISTS session_summaries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES claude_sessions(id) ON DELETE CASCADE UNIQUE,
  key_achievements TEXT[],
  challenges_overcome TEXT[],
  patterns_discovered TEXT[],
  files_modified INTEGER DEFAULT 0,
  tests_written INTEGER DEFAULT 0,
  bugs_fixed INTEGER DEFAULT 0,
  features_added INTEGER DEFAULT 0,
  duration_minutes INTEGER,
  overall_success BOOLEAN,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_session_summaries_success ON session_summaries(overall_success);
CREATE INDEX IF NOT EXISTS idx_session_summaries_created ON session_summaries(created_at DESC);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to find similar context using vector search
CREATE OR REPLACE FUNCTION find_similar_context(
  query_embedding vector(1536),
  context_filter VARCHAR(50) DEFAULT NULL,
  limit_count INTEGER DEFAULT 10
) RETURNS TABLE (
  id UUID,
  content TEXT,
  context_type VARCHAR(50),
  similarity FLOAT,
  metadata JSONB
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ce.id,
    ce.content,
    ce.context_type,
    1 - (ce.embedding <=> query_embedding) AS similarity,
    ce.metadata
  FROM context_embeddings ce
  WHERE
    (context_filter IS NULL OR ce.context_type = context_filter)
  ORDER BY ce.embedding <=> query_embedding
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update learning pattern stats
CREATE OR REPLACE FUNCTION update_pattern_stats(
  pattern_id_param UUID,
  success_param BOOLEAN,
  duration_param INTEGER
) RETURNS VOID AS $$
BEGIN
  UPDATE learning_patterns
  SET
    times_applied = times_applied + 1,
    success_rate = (
      SELECT COALESCE(
        SUM(CASE WHEN success THEN 1.0 ELSE 0.0 END) / COUNT(*),
        0
      )
      FROM pattern_applications
      WHERE pattern_id = pattern_id_param
    ),
    average_duration_ms = (
      SELECT COALESCE(AVG(duration_ms), 0)
      FROM pattern_applications
      WHERE pattern_id = pattern_id_param
    ),
    last_applied = NOW(),
    last_success = CASE WHEN success_param THEN NOW() ELSE last_success END
  WHERE id = pattern_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function to auto-generate session summary
CREATE OR REPLACE FUNCTION generate_session_summary(session_id_param UUID)
RETURNS VOID AS $$
DECLARE
  summary_data RECORD;
BEGIN
  SELECT
    COUNT(*) FILTER (WHERE context_type = 'bug_fix') as bugs,
    COUNT(*) FILTER (WHERE context_type = 'code') as files,
    COUNT(DISTINCT ai.agent_name) as agents_used,
    EXTRACT(EPOCH FROM (MAX(ai.created_at) - MIN(ai.created_at)))/60 as duration
  INTO summary_data
  FROM agent_interactions ai
  LEFT JOIN context_embeddings ce ON ce.session_id = ai.session_id
  WHERE ai.session_id = session_id_param;

  INSERT INTO session_summaries (
    session_id,
    bugs_fixed,
    files_modified,
    duration_minutes,
    overall_success
  ) VALUES (
    session_id_param,
    COALESCE(summary_data.bugs, 0),
    COALESCE(summary_data.files, 0),
    COALESCE(summary_data.duration, 0)::INTEGER,
    TRUE
  )
  ON CONFLICT (session_id) DO UPDATE SET
    bugs_fixed = EXCLUDED.bugs_fixed,
    files_modified = EXCLUDED.files_modified,
    duration_minutes = EXCLUDED.duration_minutes,
    updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS FOR AUTO-UPDATES
-- ============================================================================

-- Auto-update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_context_embeddings_updated_at
  BEFORE UPDATE ON context_embeddings
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_session_summaries_updated_at
  BEFORE UPDATE ON session_summaries
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL SEED DATA
-- ============================================================================

-- Seed common learning patterns
INSERT INTO learning_patterns (pattern_name, pattern_type, trigger_conditions, recommended_actions) VALUES
(
  'API Endpoint 500 Error',
  'bug_fix',
  '{"error_code": 500, "location": "api_endpoint"}',
  '["Check error logs", "Verify database connection", "Test with curl", "Check middleware"]'
),
(
  'Docker Build Failure',
  'deployment',
  '{"error_contains": "docker build"}',
  '["Check Dockerfile syntax", "Verify base image", "Clear docker cache", "Check .dockerignore"]'
),
(
  'Database Connection Pool Exhausted',
  'performance',
  '{"error_contains": "connection pool"}',
  '["Increase pool size", "Check for connection leaks", "Add connection recycling", "Review query performance"]'
),
(
  'Frontend Build Error',
  'bug_fix',
  '{"error_contains": ["npm", "build"]}',
  '["Clear node_modules", "Check package.json", "Verify dependencies", "Check TypeScript config"]'
),
(
  'Test Suite Failure',
  'testing',
  '{"error_contains": "test"}',
  '["Run tests individually", "Check test database", "Verify fixtures", "Review recent changes"]'
)
ON CONFLICT (pattern_name) DO NOTHING;

-- ============================================================================
-- VIEWS FOR EASY QUERYING
-- ============================================================================

-- View: Recent high-value context
CREATE OR REPLACE VIEW recent_high_value_context AS
SELECT
  ce.id,
  ce.content,
  ce.context_type,
  ce.relevance_score,
  ce.created_at,
  cs.working_directory,
  cs.active_repo
FROM context_embeddings ce
JOIN claude_sessions cs ON cs.id = ce.session_id
WHERE ce.relevance_score > 0.7
ORDER BY ce.created_at DESC
LIMIT 100;

-- View: Successful patterns
CREATE OR REPLACE VIEW successful_patterns AS
SELECT
  lp.*,
  COUNT(pa.id) as total_applications,
  AVG(pa.duration_ms) as avg_duration
FROM learning_patterns lp
LEFT JOIN pattern_applications pa ON pa.pattern_id = lp.id
WHERE lp.success_rate > 0.7
GROUP BY lp.id
ORDER BY lp.success_rate DESC, lp.times_applied DESC;

-- View: Knowledge graph connections
CREATE OR REPLACE VIEW knowledge_graph AS
SELECT
  sk1.topic as source_topic,
  sk2.topic as target_topic,
  kr.relationship_type,
  kr.strength,
  sk1.category as source_category,
  sk2.category as target_category
FROM knowledge_relationships kr
JOIN system_knowledge sk1 ON sk1.id = kr.source_knowledge_id
JOIN system_knowledge sk2 ON sk2.id = kr.target_knowledge_id
WHERE kr.strength > 0.5
ORDER BY kr.strength DESC;

-- ============================================================================
-- GRANT PERMISSIONS (if needed)
-- ============================================================================

-- Grant select on views
GRANT SELECT ON recent_high_value_context TO postgres;
GRANT SELECT ON successful_patterns TO postgres;
GRANT SELECT ON knowledge_graph TO postgres;

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '✅ Enhanced Context System Schema Deployed Successfully';
  RAISE NOTICE '   - Vector embeddings ready (pgvector 0.8.0)';
  RAISE NOTICE '   - Knowledge graph tables created';
  RAISE NOTICE '   - Decision history tracking enabled';
  RAISE NOTICE '   - Learning patterns initialized';
  RAISE NOTICE '   - Helper functions and triggers active';
  RAISE NOTICE '   - Cost: $0 (using existing Supabase pgvector)';
END $$;
