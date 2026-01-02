#!/usr/bin/env python3
"""
Vector Database Migration Script
Creates RAG system tables with pgvector support
"""

import asyncio
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

# Validate required environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")


async def run_vector_migration():
    try:
        # Use the same connection as other scripts
        import asyncpg

        conn = await asyncpg.connect(DATABASE_URL)
        
        print("🚀 Running vector database migration...")
        
        # Read and execute the migration SQL
        migration_file = os.path.join(os.path.dirname(__file__), 'migrations', '002_vector_database.sql')
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        # Execute the migration in chunks to handle large SQL
        statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement:
                try:
                    await conn.execute(statement)
                    print(f"  ✅ Executed statement {i+1}/{len(statements)}")
                except Exception as e:
                    if 'already exists' in str(e):
                        print(f"  ℹ️  Statement {i+1} - Object already exists (skipping)")
                    else:
                        print(f"  ❌ Error in statement {i+1}: {e}")
                        
        print("🎉 Vector database migration completed!")
        
        # Verify the tables were created
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN ('knowledge_base', 'rag_interactions', 'rag_metrics')
            ORDER BY tablename;
        """)
        
        print(f"\n📊 Vector tables created: {[t['tablename'] for t in tables]}")
        
        # Check if pgvector extension is available
        extensions = await conn.fetch("""
            SELECT extname FROM pg_extension WHERE extname = 'vector';
        """)
        
        if extensions:
            print("✅ pgvector extension is active")
        else:
            print("⚠️  pgvector extension not found - vector similarity search may not work")
        
        # Test basic functionality
        try:
            result = await conn.fetchval("SELECT COUNT(*) FROM knowledge_base")
            print(f"📚 Knowledge base has {result} documents")
        except Exception as e:
            print(f"⚠️  Could not query knowledge base: {e}")
        
        await conn.close()
        
    except ImportError:
        print("❌ asyncpg not available - using environment python")
        os.system('python3 /tmp/vector_migration_simple.py')
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_vector_migration())