"""
Persistent Memory System - NEVER LOSE CONTEXT
This is the brain's permanent memory - all knowledge, patterns, and learnings
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import numpy as np
from sentence_transformers import SentenceTransformer

class PersistentMemory:
    """
    The permanent brain of the system - stores everything forever
    Uses vector embeddings for semantic search and pattern recognition
    """
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db.wvkoiekcybvhpqvgqvtc.supabase.co:5432/postgres")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.initialize_schema()
        
    def initialize_schema(self):
        """Create permanent memory tables if they don't exist"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        # Core memory table with vector embeddings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS persistent_memory (
                id SERIAL PRIMARY KEY,
                memory_type VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                embedding vector(384),
                metadata JSONB DEFAULT '{}',
                importance FLOAT DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW(),
                context_id VARCHAR(100),
                INDEXES btree(memory_type),
                INDEXES gin(metadata)
            );
            
            CREATE INDEX IF NOT EXISTS idx_memory_embedding ON persistent_memory 
            USING ivfflat (embedding vector_cosine_ops);
            
            -- Learning patterns table
            CREATE TABLE IF NOT EXISTS learning_patterns (
                id SERIAL PRIMARY KEY,
                pattern_name VARCHAR(100) UNIQUE NOT NULL,
                pattern_data JSONB NOT NULL,
                confidence FLOAT DEFAULT 0.5,
                successful_applications INTEGER DEFAULT 0,
                failed_applications INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            -- System knowledge table
            CREATE TABLE IF NOT EXISTS system_knowledge (
                id SERIAL PRIMARY KEY,
                category VARCHAR(100) NOT NULL,
                key VARCHAR(200) NOT NULL,
                value JSONB NOT NULL,
                source VARCHAR(200),
                confidence FLOAT DEFAULT 1.0,
                verified BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(category, key)
            );
            
            -- User preferences and patterns
            CREATE TABLE IF NOT EXISTS user_patterns (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100),
                pattern_type VARCHAR(50),
                pattern_data JSONB NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_occurrence TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            -- Decision history for learning
            CREATE TABLE IF NOT EXISTS decision_history (
                id SERIAL PRIMARY KEY,
                decision_type VARCHAR(100) NOT NULL,
                context JSONB NOT NULL,
                decision_made JSONB NOT NULL,
                outcome JSONB,
                success_score FLOAT,
                timestamp TIMESTAMP DEFAULT NOW()
            );
            
            -- Revenue patterns and optimizations
            CREATE TABLE IF NOT EXISTS revenue_patterns (
                id SERIAL PRIMARY KEY,
                pattern_type VARCHAR(50) NOT NULL,
                conditions JSONB NOT NULL,
                action_taken JSONB NOT NULL,
                revenue_impact FLOAT,
                conversion_impact FLOAT,
                confidence FLOAT DEFAULT 0.5,
                applications INTEGER DEFAULT 0,
                last_applied TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
    def store_memory(self, content: str, memory_type: str = "general", 
                    metadata: Dict = None, importance: float = 0.5) -> int:
        """Store a memory with vector embedding"""
        # Generate embedding
        embedding = self.model.encode(content).tolist()
        
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO persistent_memory 
            (memory_type, content, embedding, metadata, importance)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (memory_type, content, embedding, Json(metadata or {}), importance))
        
        memory_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return memory_id
    
    def recall_similar(self, query: str, limit: int = 10, 
                      memory_type: Optional[str] = None) -> List[Dict]:
        """Recall memories similar to the query using vector similarity"""
        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()
        
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if memory_type:
            cursor.execute("""
                SELECT *, 
                       1 - (embedding <=> %s::vector) as similarity
                FROM persistent_memory
                WHERE memory_type = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (query_embedding, memory_type, query_embedding, limit))
        else:
            cursor.execute("""
                SELECT *, 
                       1 - (embedding <=> %s::vector) as similarity
                FROM persistent_memory
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (query_embedding, limit))
        
        memories = cursor.fetchall()
        
        # Update access count
        for memory in memories:
            cursor.execute("""
                UPDATE persistent_memory 
                SET access_count = access_count + 1,
                    last_accessed = NOW()
                WHERE id = %s
            """, (memory['id'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return memories
    
    def learn_pattern(self, pattern_name: str, pattern_data: Dict, 
                     confidence: float = 0.5):
        """Learn a new pattern or reinforce existing one"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO learning_patterns 
            (pattern_name, pattern_data, confidence)
            VALUES (%s, %s, %s)
            ON CONFLICT (pattern_name) 
            DO UPDATE SET 
                pattern_data = EXCLUDED.pattern_data,
                confidence = (learning_patterns.confidence + EXCLUDED.confidence) / 2,
                successful_applications = learning_patterns.successful_applications + 1,
                last_updated = NOW()
        """, (pattern_name, Json(pattern_data), confidence))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def apply_pattern(self, pattern_name: str, context: Dict) -> Optional[Dict]:
        """Apply a learned pattern to a new context"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM learning_patterns
            WHERE pattern_name = %s
        """, (pattern_name,))
        
        pattern = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if pattern and pattern['confidence'] > 0.3:
            return pattern['pattern_data']
        return None
    
    def store_knowledge(self, category: str, key: str, value: Any, 
                       source: str = "system", confidence: float = 1.0):
        """Store system knowledge permanently"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO system_knowledge 
            (category, key, value, source, confidence)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (category, key) 
            DO UPDATE SET 
                value = EXCLUDED.value,
                confidence = EXCLUDED.confidence,
                updated_at = NOW()
        """, (category, key, Json(value), source, confidence))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_knowledge(self, category: str, key: Optional[str] = None) -> Any:
        """Retrieve system knowledge"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if key:
            cursor.execute("""
                SELECT * FROM system_knowledge
                WHERE category = %s AND key = %s
            """, (category, key))
            result = cursor.fetchone()
        else:
            cursor.execute("""
                SELECT * FROM system_knowledge
                WHERE category = %s
            """, (category,))
            result = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return result
    
    def record_decision(self, decision_type: str, context: Dict, 
                       decision: Dict, outcome: Optional[Dict] = None):
        """Record decisions for learning"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO decision_history 
            (decision_type, context, decision_made, outcome)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (decision_type, Json(context), Json(decision), Json(outcome or {})))
        
        decision_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return decision_id
    
    def update_decision_outcome(self, decision_id: int, outcome: Dict, 
                               success_score: float):
        """Update a decision with its outcome for learning"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE decision_history
            SET outcome = %s, success_score = %s
            WHERE id = %s
        """, (Json(outcome), success_score, decision_id))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def learn_from_decisions(self, decision_type: str) -> Dict:
        """Analyze past decisions to improve future ones"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get successful decisions
        cursor.execute("""
            SELECT context, decision_made, outcome, success_score
            FROM decision_history
            WHERE decision_type = %s AND success_score > 0.7
            ORDER BY success_score DESC
            LIMIT 100
        """, (decision_type,))
        
        successful = cursor.fetchall()
        
        # Get failed decisions
        cursor.execute("""
            SELECT context, decision_made, outcome, success_score
            FROM decision_history
            WHERE decision_type = %s AND success_score < 0.3
            ORDER BY success_score ASC
            LIMIT 100
        """, (decision_type,))
        
        failed = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Extract patterns
        patterns = {
            "successful_patterns": self._extract_patterns(successful),
            "failure_patterns": self._extract_patterns(failed),
            "optimal_decisions": successful[:10] if successful else [],
            "avoid_decisions": failed[:10] if failed else []
        }
        
        return patterns
    
    def _extract_patterns(self, decisions: List[Dict]) -> List[Dict]:
        """Extract common patterns from decisions"""
        if not decisions:
            return []
        
        patterns = []
        # Group by similar contexts
        for decision in decisions:
            context_key = json.dumps(decision['context'], sort_keys=True)
            context_hash = hashlib.md5(context_key.encode()).hexdigest()[:8]
            
            patterns.append({
                "context_pattern": context_hash,
                "decision": decision['decision_made'],
                "success": decision.get('success_score', 0)
            })
        
        return patterns
    
    def store_revenue_pattern(self, pattern_type: str, conditions: Dict, 
                             action: Dict, impact: float):
        """Store successful revenue patterns"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO revenue_patterns 
            (pattern_type, conditions, action_taken, revenue_impact)
            VALUES (%s, %s, %s, %s)
        """, (pattern_type, Json(conditions), Json(action), impact))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_best_revenue_patterns(self, pattern_type: Optional[str] = None) -> List[Dict]:
        """Get the most successful revenue patterns"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if pattern_type:
            cursor.execute("""
                SELECT * FROM revenue_patterns
                WHERE pattern_type = %s AND confidence > 0.6
                ORDER BY revenue_impact DESC, confidence DESC
                LIMIT 10
            """, (pattern_type,))
        else:
            cursor.execute("""
                SELECT * FROM revenue_patterns
                WHERE confidence > 0.6
                ORDER BY revenue_impact DESC, confidence DESC
                LIMIT 20
            """)
        
        patterns = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return patterns
    
    def consolidate_memories(self):
        """Consolidate and optimize memories (like sleep for the brain)"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        # Remove low-importance, rarely accessed memories
        cursor.execute("""
            DELETE FROM persistent_memory
            WHERE importance < 0.3 
            AND access_count < 2
            AND created_at < NOW() - INTERVAL '30 days'
        """)
        
        # Boost importance of frequently accessed memories
        cursor.execute("""
            UPDATE persistent_memory
            SET importance = LEAST(importance * 1.1, 1.0)
            WHERE access_count > 10
        """)
        
        # Update pattern confidence based on success rate
        cursor.execute("""
            UPDATE learning_patterns
            SET confidence = CASE
                WHEN successful_applications > failed_applications * 2 THEN LEAST(confidence * 1.1, 1.0)
                WHEN failed_applications > successful_applications * 2 THEN GREATEST(confidence * 0.9, 0.1)
                ELSE confidence
            END
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_context_summary(self, context_id: str) -> Dict:
        """Get a summary of all memories for a specific context"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT memory_type, COUNT(*) as count, AVG(importance) as avg_importance
            FROM persistent_memory
            WHERE context_id = %s
            GROUP BY memory_type
        """, (context_id,))
        
        summary = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {"context_id": context_id, "memory_summary": summary}

# Singleton instance
memory = PersistentMemory()

# Helper functions for the AI system
def remember(content: str, importance: float = 0.5, metadata: Dict = None):
    """Quick function to store a memory"""
    return memory.store_memory(content, "general", metadata, importance)

def recall(query: str, limit: int = 5):
    """Quick function to recall memories"""
    return memory.recall_similar(query, limit)

def learn(pattern_name: str, data: Dict):
    """Quick function to learn a pattern"""
    memory.learn_pattern(pattern_name, data)

def know(category: str, key: str, value: Any):
    """Quick function to store knowledge"""
    memory.store_knowledge(category, key, value)