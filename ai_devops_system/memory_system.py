#!/usr/bin/env python3
"""
AI DevOps Persistent Memory System
Advanced memory management with vector search, conversation history, and knowledge graphs
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import uuid
import os

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlalchemy
from sqlalchemy import create_engine, text
from langchain_core.memory import BaseMemory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """Structured memory entry with metadata"""
    id: str
    content: str
    embedding: Optional[List[float]]
    timestamp: datetime
    source: str
    importance: float
    tags: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'embedding': self.embedding
        }

class VectorStore:
    """High-performance vector storage using ChromaDB and pgvector"""
    
    def __init__(self, collection_name: str = "ai_memory"):
        self.collection_name = collection_name
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize PostgreSQL connection
        self.pg_engine = self._init_postgres()
        
    def _init_postgres(self):
        """Initialize PostgreSQL with pgvector"""
        try:
            pg_url = os.getenv("PGVECTOR_DATABASE_URL")
            if not pg_url:
                raise RuntimeError("PGVECTOR_DATABASE_URL environment variable is required for PostgreSQL")
            engine = create_engine(pg_url)
            with engine.connect() as conn:
                # Create database if it doesn't exist
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS memory_vectors (
                        id VARCHAR PRIMARY KEY,
                        content TEXT,
                        embedding VECTOR(384),
                        timestamp TIMESTAMP,
                        source VARCHAR,
                        importance FLOAT,
                        tags TEXT[],
                        metadata JSONB
                    )
                """))
                conn.commit()
            return engine
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {e}. Using ChromaDB only.")
            return None
    
    def add_memory(self, entry: MemoryEntry):
        """Add memory to both ChromaDB and PostgreSQL"""
        if entry.embedding is None:
            entry.embedding = self.model.encode(entry.content).tolist()
        
        # Add to ChromaDB
        self.collection.add(
            embeddings=[entry.embedding],
            documents=[entry.content],
            metadatas=[{
                'timestamp': entry.timestamp.isoformat(),
                'source': entry.source,
                'importance': entry.importance,
                'tags': ','.join(entry.tags)
            }],
            ids=[entry.id]
        )
        
        # Add to PostgreSQL if available
        if self.pg_engine:
            try:
                with self.pg_engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO memory_vectors 
                        (id, content, embedding, timestamp, source, importance, tags, metadata)
                        VALUES (:id, :content, :embedding, :timestamp, :source, :importance, :tags, :metadata)
                        ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        timestamp = EXCLUDED.timestamp,
                        importance = EXCLUDED.importance,
                        tags = EXCLUDED.tags,
                        metadata = EXCLUDED.metadata
                    """), {
                        'id': entry.id,
                        'content': entry.content,
                        'embedding': entry.embedding,
                        'timestamp': entry.timestamp,
                        'source': entry.source,
                        'importance': entry.importance,
                        'tags': entry.tags,
                        'metadata': json.dumps(entry.metadata)
                    })
                    conn.commit()
            except Exception as e:
                logger.error(f"Failed to add to PostgreSQL: {e}")
    
    def search_similar(self, query: str, n_results: int = 10, threshold: float = 0.7) -> List[Dict]:
        """Search for similar memories"""
        query_embedding = self.model.encode(query).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        memories = []
        if results['documents'][0]:
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                if distance <= (1 - threshold):  # ChromaDB uses distance, we want similarity
                    memories.append({
                        'content': doc,
                        'metadata': metadata,
                        'similarity': 1 - distance
                    })
        
        return sorted(memories, key=lambda x: x['similarity'], reverse=True)

class ConversationMemory:
    """Manages conversation history with summarization"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.conversation_key = "conversation_history"
        self.max_messages = 100
        
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add message to conversation history"""
        message = {
            'id': str(uuid.uuid4()),
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.redis.lpush(self.conversation_key, json.dumps(message))
        self.redis.ltrim(self.conversation_key, 0, self.max_messages - 1)
        
    def get_recent_messages(self, n: int = 20) -> List[Dict]:
        """Get recent conversation messages"""
        messages = self.redis.lrange(self.conversation_key, 0, n - 1)
        return [json.loads(msg) for msg in messages]
    
    def get_conversation_summary(self) -> str:
        """Generate conversation summary for long-term memory"""
        messages = self.get_recent_messages(50)
        if not messages:
            return "No conversation history"
        
        # Simple summarization logic
        human_messages = [msg['content'] for msg in messages if msg['role'] == 'human']
        ai_messages = [msg['content'] for msg in messages if msg['role'] == 'assistant']
        
        return f"Recent conversation covered {len(human_messages)} user queries with {len(ai_messages)} responses"

class KnowledgeGraph:
    """Simple knowledge graph for entity relationships"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.entities_key = "knowledge_entities"
        self.relations_key = "knowledge_relations"
        
    def add_entity(self, entity_id: str, entity_type: str, properties: Dict):
        """Add entity to knowledge graph"""
        entity_data = {
            'id': entity_id,
            'type': entity_type,
            'properties': properties,
            'created_at': datetime.now().isoformat()
        }
        
        self.redis.hset(self.entities_key, entity_id, json.dumps(entity_data))
        
    def add_relation(self, entity1_id: str, relation_type: str, entity2_id: str, properties: Dict = None):
        """Add relationship between entities"""
        relation_id = f"{entity1_id}:{relation_type}:{entity2_id}"
        relation_data = {
            'id': relation_id,
            'entity1': entity1_id,
            'relation': relation_type,
            'entity2': entity2_id,
            'properties': properties or {},
            'created_at': datetime.now().isoformat()
        }
        
        self.redis.hset(self.relations_key, relation_id, json.dumps(relation_data))
        
    def get_entity_relations(self, entity_id: str) -> List[Dict]:
        """Get all relations for an entity"""
        relations = []
        all_relations = self.redis.hgetall(self.relations_key)
        
        for rel_id, rel_data in all_relations.items():
            rel_dict = json.loads(rel_data)
            if entity_id in [rel_dict['entity1'], rel_dict['entity2']]:
                relations.append(rel_dict)
                
        return relations

class PersistentMemorySystem:
    """Main memory system coordinating all components"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.conversation_memory = ConversationMemory(self.redis_client)
        self.knowledge_graph = KnowledgeGraph(self.redis_client)
        
        # Memory importance scoring
        self.importance_weights = {
            'recency': 0.3,
            'frequency': 0.3,
            'relevance': 0.4
        }
        
    def store_memory(self, content: str, source: str = "user", tags: List[str] = None, 
                    importance: float = None, metadata: Dict = None) -> str:
        """Store a new memory"""
        memory_id = str(uuid.uuid4())
        
        if importance is None:
            importance = self._calculate_importance(content, source)
            
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            embedding=None,  # Will be generated in vector_store
            timestamp=datetime.now(),
            source=source,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.vector_store.add_memory(entry)
        logger.info(f"Stored memory: {memory_id}")
        return memory_id
    
    def retrieve_memories(self, query: str, n_results: int = 5) -> List[Dict]:
        """Retrieve relevant memories"""
        # Get similar memories from vector store
        similar_memories = self.vector_store.search_similar(query, n_results * 2)
        
        # Re-rank by importance and recency
        ranked_memories = []
        for memory in similar_memories:
            # Parse timestamp
            timestamp_str = memory['metadata'].get('timestamp', '')
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                recency_score = self._calculate_recency_score(timestamp)
            except:
                recency_score = 0.1
                
            importance = float(memory['metadata'].get('importance', 0.5))
            similarity = memory['similarity']
            
            combined_score = (
                similarity * self.importance_weights['relevance'] +
                importance * self.importance_weights['frequency'] +
                recency_score * self.importance_weights['recency']
            )
            
            memory['combined_score'] = combined_score
            ranked_memories.append(memory)
        
        return sorted(ranked_memories, key=lambda x: x['combined_score'], reverse=True)[:n_results]
    
    def add_conversation_turn(self, human_input: str, ai_response: str, metadata: Dict = None):
        """Add a conversation turn to memory"""
        # Store individual messages in conversation memory
        self.conversation_memory.add_message("human", human_input, metadata)
        self.conversation_memory.add_message("assistant", ai_response, metadata)
        
        # Store important conversations in long-term memory
        conversation_importance = self._calculate_importance(f"{human_input} {ai_response}", "conversation")
        if conversation_importance > 0.6:
            self.store_memory(
                content=f"User: {human_input}\nAssistant: {ai_response}",
                source="conversation",
                tags=["conversation", "important"],
                importance=conversation_importance,
                metadata=metadata
            )
    
    def get_conversation_context(self, n_messages: int = 10) -> str:
        """Get recent conversation context"""
        messages = self.conversation_memory.get_recent_messages(n_messages)
        
        context_parts = []
        for msg in reversed(messages):  # Reverse to get chronological order
            role = "Human" if msg['role'] == 'human' else "Assistant"
            context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def _calculate_importance(self, content: str, source: str) -> float:
        """Calculate memory importance score"""
        base_score = 0.5
        
        # Source-based importance
        source_weights = {
            "user": 0.8,
            "conversation": 0.7,
            "system": 0.6,
            "background": 0.3
        }
        source_score = source_weights.get(source, 0.5)
        
        # Content-based importance
        important_keywords = [
            "error", "critical", "important", "remember", "key", "crucial",
            "problem", "solution", "bug", "fix", "urgent", "priority"
        ]
        
        keyword_score = sum(1 for keyword in important_keywords if keyword.lower() in content.lower())
        keyword_score = min(keyword_score * 0.1, 0.3)
        
        # Length-based importance (longer content might be more important)
        length_score = min(len(content) / 1000, 0.2)
        
        final_score = base_score + source_score * 0.3 + keyword_score + length_score
        return min(final_score, 1.0)
    
    def _calculate_recency_score(self, timestamp: datetime) -> float:
        """Calculate recency score (more recent = higher score)"""
        now = datetime.now()
        time_diff = now - timestamp
        
        # Score decreases with time
        hours_ago = time_diff.total_seconds() / 3600
        if hours_ago < 1:
            return 1.0
        elif hours_ago < 24:
            return 0.8
        elif hours_ago < 168:  # 1 week
            return 0.6
        elif hours_ago < 720:  # 1 month
            return 0.4
        else:
            return 0.2
    
    def cleanup_old_memories(self, days_threshold: int = 30):
        """Clean up old, low-importance memories"""
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        # This would require implementing deletion in ChromaDB and PostgreSQL
        # For now, just log the action
        logger.info(f"Memory cleanup: would remove memories older than {cutoff_date}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        try:
            total_memories = self.vector_store.collection.count()
            conversation_length = self.redis_client.llen(self.conversation_memory.conversation_key)
            entities_count = self.redis_client.hlen(self.knowledge_graph.entities_key)
            relations_count = self.redis_client.hlen(self.knowledge_graph.relations_key)
            
            return {
                "total_memories": total_memories,
                "conversation_messages": conversation_length,
                "knowledge_entities": entities_count,
                "knowledge_relations": relations_count,
                "system_status": "healthy"
            }
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"system_status": "error", "error": str(e)}

# Example usage and testing
if __name__ == "__main__":
    # Initialize memory system
    memory = PersistentMemorySystem()
    
    # Test storing memories
    memory.store_memory(
        "The user prefers Python for data science tasks",
        source="user",
        tags=["preference", "programming"],
        metadata={"confidence": 0.9}
    )
    
    memory.store_memory(
        "PostgreSQL connection failed, using ChromaDB fallback",
        source="system",
        tags=["error", "database"],
        metadata={"error_code": "CONNECTION_FAILED"}
    )
    
    # Test conversation memory
    memory.add_conversation_turn(
        "How do I set up a vector database?",
        "I recommend using ChromaDB for local development. Here's how to install it...",
        metadata={"topic": "vector_database"}
    )
    
    # Test memory retrieval
    results = memory.retrieve_memories("database setup")
    print("Retrieved memories:")
    for result in results:
        print(f"- {result['content'][:100]}... (score: {result['combined_score']:.3f})")
    
    # Get conversation context
    context = memory.get_conversation_context()
    print("\nConversation context:")
    print(context)
    
    # Get system stats
    stats = memory.get_memory_stats()
    print(f"\nMemory system stats: {stats}")