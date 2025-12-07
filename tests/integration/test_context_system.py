"""
Integration Tests - Enhanced Context System
Tests for vector embeddings, semantic search, learning patterns
"""

import pytest
import psycopg2

@pytest.mark.integration
@pytest.mark.database
async def test_context_embeddings_table_exists(async_db_pool):
    """Test context_embeddings table exists and is accessible"""
    async with async_db_pool.acquire() as conn:
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename = 'context_embeddings'
            )
        """)
        assert result is True

@pytest.mark.integration
@pytest.mark.database
async def test_insert_context_embedding(async_db_pool):
    """Test inserting context embedding"""
    async with async_db_pool.acquire() as conn:
        # Insert test embedding
        embedding_id = await conn.fetchval("""
            INSERT INTO context_embeddings (content, context_type)
            VALUES ($1, $2)
            RETURNING id
        """, "Test context content", "code")

        assert embedding_id is not None

        # Clean up
        await conn.execute("DELETE FROM context_embeddings WHERE id = $1", embedding_id)

@pytest.mark.integration
@pytest.mark.database
async def test_knowledge_relationships_table(async_db_pool):
    """Test knowledge relationships table"""
    async with async_db_pool.acquire() as conn:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename = 'knowledge_relationships'
            )
        """)
        assert exists is True

@pytest.mark.integration
@pytest.mark.database
async def test_decision_history_table(async_db_pool):
    """Test decision history table"""
    async with async_db_pool.acquire() as conn:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename = 'decision_history'
            )
        """)
        assert exists is True

@pytest.mark.integration
@pytest.mark.database
async def test_learning_patterns_seeded(async_db_pool):
    """Test learning patterns have seed data"""
    async with async_db_pool.acquire() as conn:
        count = await conn.fetchval("""
            SELECT COUNT(*) FROM learning_patterns
        """)
        # Should have at least the seed patterns
        assert count > 0

@pytest.mark.integration
@pytest.mark.database
@pytest.mark.slow
async def test_vector_search_function(async_db_pool, mock_openai_embedding):
    """Test vector similarity search function"""
    async with async_db_pool.acquire() as conn:
        # Insert test embedding
        # pgvector expects bracketed arrays: [0.1,0.2,...]
        embedding_str = "[" + ",".join(str(x) for x in mock_openai_embedding) + "]"
        embedding_id = await conn.fetchval("""
            INSERT INTO context_embeddings (content, embedding, context_type)
            VALUES ($1, $2::vector, $3)
            RETURNING id
        """, "Test semantic search", embedding_str, "code")

        # Test similarity search (should find itself)
        results = await conn.fetch("""
            SELECT content, 1 - (embedding <=> $1::vector) as similarity
            FROM context_embeddings
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT 1
        """, embedding_str)

        assert len(results) > 0
        assert results[0]['similarity'] > 0.99  # Should be nearly identical

        # Clean up
        await conn.execute("DELETE FROM context_embeddings WHERE id = $1", embedding_id)

@pytest.mark.integration
@pytest.mark.ci
async def test_session_summaries_table(async_db_pool):
    """Test session summaries table"""
    async with async_db_pool.acquire() as conn:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename = 'session_summaries'
            )
        """)
        assert exists is True
