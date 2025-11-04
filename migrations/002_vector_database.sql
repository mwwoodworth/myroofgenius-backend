-- Vector Database Setup for RAG Implementation
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge base table for storing documents and embeddings
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text', -- text, markdown, pdf, etc.
    category VARCHAR(100) NOT NULL, -- roofing_materials, regulations, safety, etc.
    subcategory VARCHAR(100),
    source VARCHAR(255), -- URL, file path, or source identifier
    embedding vector(1536), -- OpenAI ada-002 embedding size
    metadata JSONB DEFAULT '{}'::jsonb,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    chunk_index INTEGER DEFAULT 0, -- For documents split into chunks
    parent_document_id UUID REFERENCES knowledge_base(id),
    
    -- Content quality and relevance
    quality_score FLOAT DEFAULT 0.8,
    relevance_score FLOAT DEFAULT 1.0,
    view_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT NOW(),
    
    -- Administrative fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(100) DEFAULT 'system'
);

-- Create vector index for similarity search
CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx 
ON knowledge_base USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 1000);

-- Create other useful indices
CREATE INDEX IF NOT EXISTS idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_subcategory ON knowledge_base(subcategory);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_content_type ON knowledge_base(content_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_quality ON knowledge_base(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_tags ON knowledge_base USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_metadata ON knowledge_base USING GIN(metadata);

-- RAG queries and responses table for learning
CREATE TABLE IF NOT EXISTS rag_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    query_embedding vector(1536),
    query_intent VARCHAR(100), -- estimation, safety, materials, regulations, etc.
    
    -- Retrieved documents
    retrieved_documents JSONB, -- Array of document IDs and scores
    context_used TEXT, -- The actual context sent to LLM
    
    -- Generated response
    response_text TEXT,
    response_quality_score FLOAT,
    response_time_ms INTEGER,
    
    -- User interaction
    user_feedback INTEGER, -- 1-5 rating
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    
    -- Source tracking
    source_endpoint VARCHAR(100), -- Which API endpoint was used
    model_used VARCHAR(50) DEFAULT 'gpt-4',
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- RAG performance metrics
CREATE TABLE IF NOT EXISTS rag_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE DEFAULT CURRENT_DATE,
    
    -- Query metrics
    total_queries INTEGER DEFAULT 0,
    avg_response_time_ms FLOAT,
    avg_quality_score FLOAT,
    
    -- Retrieval metrics
    avg_documents_retrieved FLOAT,
    avg_similarity_score FLOAT,
    
    -- Popular categories
    top_categories JSONB,
    
    -- Performance by intent
    metrics_by_intent JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date)
);

-- Roofing knowledge categories seeding
INSERT INTO knowledge_base (title, content, category, subcategory, tags, quality_score) VALUES
    ('Asphalt Shingle Installation', 
     'Standard installation procedure for asphalt shingles including proper overlap, fastening patterns, and weather sealing techniques...', 
     'installation', 'asphalt_shingles', 
     ARRAY['installation', 'asphalt', 'shingles', 'roofing'], 
     0.95),
     
    ('Metal Roofing Safety Protocols', 
     'Safety requirements and best practices for metal roof installation including fall protection, tool safety, and weather considerations...', 
     'safety', 'metal_roofing', 
     ARRAY['safety', 'metal', 'protocols', 'OSHA'], 
     0.90),
     
    ('Flat Roof Drainage Systems', 
     'Proper drainage design for flat commercial roofs including slope calculations, drain placement, and overflow provisions...', 
     'design', 'flat_roof', 
     ARRAY['drainage', 'flat roof', 'commercial', 'design'], 
     0.88),
     
    ('Roofing Material Cost Analysis', 
     'Current market pricing for common roofing materials including regional variations and bulk pricing strategies...', 
     'cost_estimation', 'materials', 
     ARRAY['cost', 'materials', 'pricing', 'estimation'], 
     0.92),
     
    ('Building Code Requirements 2024', 
     'Updated building code requirements for residential and commercial roofing including ventilation, fire resistance, and structural requirements...', 
     'regulations', 'building_codes', 
     ARRAY['building codes', 'regulations', '2024', 'compliance'], 
     0.96);

-- Function to search knowledge base with vector similarity
CREATE OR REPLACE FUNCTION search_knowledge_base(
    query_embedding vector(1536),
    category_filter VARCHAR DEFAULT NULL,
    limit_results INTEGER DEFAULT 5,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    title VARCHAR,
    content TEXT,
    category VARCHAR,
    subcategory VARCHAR,
    similarity_score FLOAT,
    metadata JSONB,
    tags TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        kb.id,
        kb.title,
        kb.content,
        kb.category,
        kb.subcategory,
        1 - (kb.embedding <=> query_embedding) as similarity_score,
        kb.metadata,
        kb.tags
    FROM knowledge_base kb
    WHERE 
        kb.is_active = true
        AND (category_filter IS NULL OR kb.category = category_filter)
        AND (1 - (kb.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY kb.embedding <=> query_embedding
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Function to log RAG interactions
CREATE OR REPLACE FUNCTION log_rag_interaction(
    p_query_text TEXT,
    p_query_embedding vector(1536),
    p_query_intent VARCHAR,
    p_retrieved_docs JSONB,
    p_context_used TEXT,
    p_response_text TEXT,
    p_response_time INTEGER,
    p_user_id VARCHAR DEFAULT NULL,
    p_session_id VARCHAR DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    interaction_id UUID;
BEGIN
    INSERT INTO rag_interactions (
        query_text,
        query_embedding, 
        query_intent,
        retrieved_documents,
        context_used,
        response_text,
        response_time_ms,
        user_id,
        session_id
    ) VALUES (
        p_query_text,
        p_query_embedding,
        p_query_intent,
        p_retrieved_docs,
        p_context_used,
        p_response_text,
        p_response_time,
        p_user_id,
        p_session_id
    )
    RETURNING id INTO interaction_id;
    
    RETURN interaction_id;
END;
$$ LANGUAGE plpgsql;

-- Daily metrics update function
CREATE OR REPLACE FUNCTION update_daily_rag_metrics()
RETURNS VOID AS $$
DECLARE
    today DATE := CURRENT_DATE;
BEGIN
    INSERT INTO rag_metrics (
        date,
        total_queries,
        avg_response_time_ms,
        avg_quality_score,
        avg_documents_retrieved,
        top_categories
    )
    SELECT 
        today,
        COUNT(*) as total_queries,
        AVG(response_time_ms) as avg_response_time_ms,
        AVG(response_quality_score) as avg_quality_score,
        AVG(jsonb_array_length(retrieved_documents)) as avg_documents_retrieved,
        jsonb_agg(DISTINCT jsonb_build_object('intent', query_intent, 'count', count_by_intent.cnt))
    FROM rag_interactions ri
    LEFT JOIN (
        SELECT query_intent, COUNT(*) as cnt
        FROM rag_interactions 
        WHERE created_at::date = today
        GROUP BY query_intent
    ) count_by_intent ON ri.query_intent = count_by_intent.query_intent
    WHERE ri.created_at::date = today
    ON CONFLICT (date) DO UPDATE SET
        total_queries = EXCLUDED.total_queries,
        avg_response_time_ms = EXCLUDED.avg_response_time_ms,
        avg_quality_score = EXCLUDED.avg_quality_score,
        avg_documents_retrieved = EXCLUDED.avg_documents_retrieved,
        top_categories = EXCLUDED.top_categories;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE knowledge_base IS 'Vector database for RAG implementation storing documents with embeddings';
COMMENT ON TABLE rag_interactions IS 'Log of all RAG queries and responses for learning and optimization';
COMMENT ON TABLE rag_metrics IS 'Daily performance metrics for RAG system monitoring';
COMMENT ON FUNCTION search_knowledge_base IS 'Vector similarity search function for knowledge base';
COMMENT ON FUNCTION log_rag_interaction IS 'Log RAG query/response interaction for analytics';
COMMENT ON FUNCTION update_daily_rag_metrics IS 'Update daily RAG performance metrics';