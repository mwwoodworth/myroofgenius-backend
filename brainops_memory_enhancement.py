"""
BrainOps Persistent Memory System Enhancement
Advanced memory management with vector embeddings and human-like memory dynamics
"""

import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
from dataclasses import dataclass, field
import asyncio
import logging

# Database imports
import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Vector similarity imports (with fallback)
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("FAISS not available, using cosine similarity fallback")

# Embeddings (with fallback)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not available, using hash-based embeddings fallback")

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """Types of memory in the system"""
    WORKING = "working"  # Temporary, session-based
    EPISODIC = "episodic"  # Specific events/experiences
    SEMANTIC = "semantic"  # Facts and knowledge
    PROCEDURAL = "procedural"  # How to do things
    EMOTIONAL = "emotional"  # User preferences, feelings
    META = "meta"  # Self-reflection, improvements

class ImportanceLevel(Enum):
    """Memory importance hierarchy"""
    CRITICAL = 1.0  # Never forget (passwords, keys, critical config)
    HIGH = 0.8      # Important context
    MEDIUM = 0.5    # Regular information
    LOW = 0.3       # Nice to have
    TRIVIAL = 0.1   # Can be forgotten

@dataclass
class Memory:
    """Enhanced memory structure with decay and reinforcement"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    memory_type: MemoryType = MemoryType.SEMANTIC
    importance: float = ImportanceLevel.MEDIUM.value
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    decay_rate: float = 0.01  # Ebbinghaus forgetting curve factor
    reinforcement_count: int = 0
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    associations: List[str] = field(default_factory=list)  # Related memory IDs
    context: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    def calculate_strength(self, current_time: datetime = None) -> float:
        """Calculate memory strength using forgetting curve and reinforcement"""
        if current_time is None:
            current_time = datetime.utcnow()

        # Time since last access in hours
        time_delta = (current_time - self.last_accessed).total_seconds() / 3600

        # Ebbinghaus forgetting curve: R = e^(-t/S)
        # Where S is stability (influenced by importance and reinforcement)
        stability = (self.importance * 10) + (self.reinforcement_count * 2)
        retention = np.exp(-time_delta * self.decay_rate / stability)

        # Boost retention based on access frequency
        frequency_boost = min(1.0, self.access_count * 0.1)

        # Final strength combines retention, importance, and frequency
        strength = (retention * 0.5) + (self.importance * 0.3) + (frequency_boost * 0.2)

        return min(1.0, strength)

    def reinforce(self):
        """Strengthen memory through access"""
        self.access_count += 1
        self.reinforcement_count += 1
        self.last_accessed = datetime.utcnow()
        # Reduce decay rate with reinforcement
        self.decay_rate = max(0.001, self.decay_rate * 0.95)

class BrainOpsMemorySystem:
    """Enhanced persistent memory system with vector search and human-like dynamics"""

    def __init__(self, db_url: str = None, openai_key: str = None):
        """Initialize the memory system"""
        self.db_url = db_url or os.getenv('DATABASE_URL')
        self.openai_key = openai_key or os.getenv('OPENAI_API_KEY')

        # Memory storage
        self.working_memory: Dict[str, Memory] = {}
        self.long_term_memory: Dict[str, Memory] = {}
        self.memory_index = None
        self.embeddings_cache: Dict[str, np.ndarray] = {}

        # Initialize components
        self._init_database()
        self._init_vector_store()
        self._init_embeddings()
        self._load_existing_memories()

        # Configuration
        self.consolidation_threshold = 0.7  # Strength needed for long-term storage
        self.max_working_memory = 100
        self.forget_threshold = 0.1  # Memories below this strength are forgotten

        logger.info("BrainOps Memory System initialized")

    def _init_database(self):
        """Initialize database connection"""
        if self.db_url:
            try:
                self.engine = create_engine(self.db_url)
                self.SessionLocal = sessionmaker(bind=self.engine)
                logger.info("Database connection established")
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                self.engine = None
                self.SessionLocal = None
        else:
            self.engine = None
            self.SessionLocal = None

    def _init_vector_store(self):
        """Initialize FAISS vector store for similarity search"""
        if FAISS_AVAILABLE:
            # 1536 dimensions for OpenAI embeddings, 768 for fallback
            self.embedding_dim = 1536 if OPENAI_AVAILABLE else 768
            self.memory_index = faiss.IndexFlatL2(self.embedding_dim)
            logger.info("FAISS vector store initialized")
        else:
            self.memory_index = None
            logger.info("Using fallback similarity search")

    def _init_embeddings(self):
        """Initialize embedding generator"""
        if OPENAI_AVAILABLE and self.openai_key:
            self.openai_client = OpenAI(api_key=self.openai_key)
            logger.info("OpenAI embeddings initialized")
        else:
            self.openai_client = None
            logger.info("Using fallback embeddings")

    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        # Check cache first
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.embeddings_cache:
            return self.embeddings_cache[text_hash]

        embedding = None

        # Try OpenAI first
        if self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    input=text,
                    model="text-embedding-3-small"
                )
                embedding = np.array(response.data[0].embedding)
            except Exception as e:
                logger.error(f"OpenAI embedding failed: {e}")

        # Fallback to hash-based embedding
        if embedding is None:
            # Create deterministic embedding from text
            np.random.seed(int(hashlib.md5(text.encode()).hexdigest()[:8], 16))
            dim = 1536 if OPENAI_AVAILABLE else 768
            embedding = np.random.randn(dim).astype('float32')
            embedding = embedding / np.linalg.norm(embedding)

        # Cache the embedding
        self.embeddings_cache[text_hash] = embedding
        return embedding

    def _load_existing_memories(self):
        """Load existing memories from database"""
        if not self.SessionLocal:
            return

        try:
            with self.SessionLocal() as session:
                result = session.execute(text("""
                    SELECT id, content, metadata, importance, created_at,
                           last_accessed, access_count, memory_type, tags
                    FROM brainops_memory
                    WHERE active = true
                    ORDER BY importance DESC, last_accessed DESC
                    LIMIT 1000
                """))

                for row in result:
                    memory = Memory(
                        id=str(row.id),
                        content=row.content,
                        memory_type=MemoryType(row.memory_type) if row.memory_type else MemoryType.SEMANTIC,
                        importance=row.importance or 0.5,
                        created_at=row.created_at,
                        last_accessed=row.last_accessed or row.created_at,
                        access_count=row.access_count or 0,
                        metadata=row.metadata or {},
                        tags=row.tags if hasattr(row, 'tags') else []
                    )

                    # Generate embedding
                    memory.embedding = self._generate_embedding(memory.content)

                    # Store in long-term memory
                    self.long_term_memory[memory.id] = memory

                    # Add to vector index if available
                    if self.memory_index and memory.embedding is not None:
                        self.memory_index.add(memory.embedding.reshape(1, -1))

                logger.info(f"Loaded {len(self.long_term_memory)} existing memories")
        except Exception as e:
            logger.error(f"Failed to load existing memories: {e}")

    def store(self,
              content: str,
              memory_type: MemoryType = MemoryType.SEMANTIC,
              importance: float = ImportanceLevel.MEDIUM.value,
              metadata: Dict[str, Any] = None,
              tags: List[str] = None) -> Memory:
        """Store a new memory"""
        memory = Memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata or {},
            tags=tags or []
        )

        # Generate embedding
        memory.embedding = self._generate_embedding(content)

        # Store in working memory first
        self.working_memory[memory.id] = memory

        # If important enough, directly store in long-term
        if importance >= ImportanceLevel.HIGH.value:
            self._consolidate_memory(memory)

        # Manage working memory size
        self._manage_working_memory()

        # Persist to database
        self._persist_memory(memory)

        return memory

    def recall(self,
               query: str,
               memory_types: List[MemoryType] = None,
               limit: int = 10,
               min_relevance: float = 0.3) -> List[Tuple[Memory, float]]:
        """Recall relevant memories using semantic search"""
        query_embedding = self._generate_embedding(query)

        # Search in both working and long-term memory
        all_memories = {**self.working_memory, **self.long_term_memory}

        # Filter by memory type if specified
        if memory_types:
            all_memories = {
                k: v for k, v in all_memories.items()
                if v.memory_type in memory_types
            }

        # Calculate relevance scores
        scored_memories = []
        for memory in all_memories.values():
            if memory.embedding is not None:
                # Cosine similarity
                similarity = np.dot(query_embedding, memory.embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(memory.embedding)
                )

                # Combine with memory strength
                strength = memory.calculate_strength()
                relevance = (similarity * 0.7) + (strength * 0.3)

                if relevance >= min_relevance:
                    scored_memories.append((memory, relevance))
                    # Reinforce accessed memory
                    memory.reinforce()

        # Sort by relevance and return top results
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return scored_memories[:limit]

    def reason(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Multi-step reasoning with memory chain"""
        thoughts = []
        evidence = []

        # Step 1: Recall relevant memories
        thoughts.append(f"Searching for memories related to: {query}")
        relevant_memories = self.recall(query, limit=5)

        for memory, relevance in relevant_memories:
            evidence.append({
                "content": memory.content,
                "relevance": relevance,
                "type": memory.memory_type.value,
                "confidence": memory.confidence
            })
            thoughts.append(f"Found relevant {memory.memory_type.value}: {memory.content[:100]}...")

        # Step 2: Check for conflicting information
        conflicts = self._detect_conflicts(relevant_memories)
        if conflicts:
            thoughts.append(f"Detected {len(conflicts)} conflicting memories")
            # Resolve conflicts based on recency and confidence
            resolved = self._resolve_conflicts(conflicts)
            thoughts.append(f"Resolved conflicts using recency and confidence")
            evidence = resolved

        # Step 3: Form conclusions
        conclusions = []
        overall_confidence = 0.0

        if evidence:
            # Weight evidence by relevance and confidence
            total_weight = sum(e["relevance"] * e["confidence"] for e in evidence)

            for e in evidence:
                weight = (e["relevance"] * e["confidence"]) / total_weight if total_weight > 0 else 0
                conclusions.append({
                    "fact": e["content"],
                    "weight": weight
                })
                overall_confidence += weight * e["confidence"]

            thoughts.append(f"Formed {len(conclusions)} conclusions with {overall_confidence:.2f} confidence")
        else:
            thoughts.append("No relevant memories found for this query")

        # Step 4: Store the reasoning chain
        reasoning_memory = self.store(
            content=json.dumps({
                "query": query,
                "conclusions": conclusions,
                "confidence": overall_confidence
            }),
            memory_type=MemoryType.META,
            importance=ImportanceLevel.MEDIUM.value,
            metadata={"thoughts": thoughts, "context": context}
        )

        return {
            "query": query,
            "thoughts": thoughts,
            "evidence": evidence,
            "conclusions": conclusions,
            "confidence": overall_confidence,
            "memory_id": reasoning_memory.id
        }

    def _consolidate_memory(self, memory: Memory):
        """Move memory from working to long-term storage"""
        # Add to long-term memory
        self.long_term_memory[memory.id] = memory

        # Remove from working memory if present
        if memory.id in self.working_memory:
            del self.working_memory[memory.id]

        # Add to vector index
        if self.memory_index and memory.embedding is not None:
            self.memory_index.add(memory.embedding.reshape(1, -1))

        logger.debug(f"Consolidated memory {memory.id} to long-term storage")

    def _manage_working_memory(self):
        """Manage working memory size and consolidation"""
        # Check for memories to consolidate
        for memory_id, memory in list(self.working_memory.items()):
            strength = memory.calculate_strength()

            # Consolidate strong memories
            if strength >= self.consolidation_threshold:
                self._consolidate_memory(memory)
            # Forget weak memories
            elif strength < self.forget_threshold:
                del self.working_memory[memory_id]
                logger.debug(f"Forgot weak memory {memory_id}")

        # If still over limit, remove oldest weak memories
        if len(self.working_memory) > self.max_working_memory:
            sorted_memories = sorted(
                self.working_memory.items(),
                key=lambda x: x[1].calculate_strength()
            )

            for memory_id, _ in sorted_memories[:len(self.working_memory) - self.max_working_memory]:
                del self.working_memory[memory_id]
                logger.debug(f"Evicted memory {memory_id} due to size limit")

    def _detect_conflicts(self, memories: List[Tuple[Memory, float]]) -> List[List[Memory]]:
        """Detect conflicting memories"""
        conflicts = []
        # Simple conflict detection based on semantic similarity of facts
        # In production, this would use more sophisticated NLP
        return conflicts

    def _resolve_conflicts(self, conflicts: List[List[Memory]]) -> List[Dict[str, Any]]:
        """Resolve conflicting memories based on recency and confidence"""
        resolved = []
        for conflict_group in conflicts:
            # Sort by recency and confidence
            conflict_group.sort(
                key=lambda m: (m.last_accessed, m.confidence),
                reverse=True
            )
            # Take the most recent, high-confidence memory
            best = conflict_group[0]
            resolved.append({
                "content": best.content,
                "relevance": 1.0,
                "type": best.memory_type.value,
                "confidence": best.confidence
            })
        return resolved

    def _persist_memory(self, memory: Memory):
        """Persist memory to database"""
        if not self.SessionLocal:
            return

        try:
            with self.SessionLocal() as session:
                # Convert embedding to list for JSON storage
                embedding_list = memory.embedding.tolist() if memory.embedding is not None else None

                session.execute(text("""
                    INSERT INTO brainops_memory (
                        id, content, memory_type, importance, metadata,
                        tags, created_at, last_accessed, access_count,
                        decay_rate, reinforcement_count, embedding
                    ) VALUES (
                        :id, :content, :memory_type, :importance, :metadata,
                        :tags, :created_at, :last_accessed, :access_count,
                        :decay_rate, :reinforcement_count, :embedding
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        last_accessed = :last_accessed,
                        access_count = :access_count,
                        reinforcement_count = :reinforcement_count,
                        decay_rate = :decay_rate
                """), {
                    "id": memory.id,
                    "content": memory.content,
                    "memory_type": memory.memory_type.value,
                    "importance": memory.importance,
                    "metadata": json.dumps(memory.metadata),
                    "tags": memory.tags,
                    "created_at": memory.created_at,
                    "last_accessed": memory.last_accessed,
                    "access_count": memory.access_count,
                    "decay_rate": memory.decay_rate,
                    "reinforcement_count": memory.reinforcement_count,
                    "embedding": json.dumps(embedding_list) if embedding_list else None
                })
                session.commit()
                logger.debug(f"Persisted memory {memory.id}")
        except Exception as e:
            logger.error(f"Failed to persist memory: {e}")

    def forget_irrelevant(self, threshold: float = 0.1):
        """Forget memories below relevance threshold"""
        forgotten = []

        for memory_id, memory in list(self.long_term_memory.items()):
            if memory.calculate_strength() < threshold:
                del self.long_term_memory[memory_id]
                forgotten.append(memory_id)

                # Mark as inactive in database
                if self.SessionLocal:
                    try:
                        with self.SessionLocal() as session:
                            session.execute(text("""
                                UPDATE brainops_memory
                                SET active = false
                                WHERE id = :id
                            """), {"id": memory_id})
                            session.commit()
                    except Exception as e:
                        logger.error(f"Failed to mark memory as inactive: {e}")

        logger.info(f"Forgot {len(forgotten)} irrelevant memories")
        return forgotten

    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        working_stats = {}
        for memory_type in MemoryType:
            working_stats[memory_type.value] = sum(
                1 for m in self.working_memory.values()
                if m.memory_type == memory_type
            )

        long_term_stats = {}
        for memory_type in MemoryType:
            long_term_stats[memory_type.value] = sum(
                1 for m in self.long_term_memory.values()
                if m.memory_type == memory_type
            )

        return {
            "working_memory": {
                "total": len(self.working_memory),
                "by_type": working_stats
            },
            "long_term_memory": {
                "total": len(self.long_term_memory),
                "by_type": long_term_stats
            },
            "embeddings_cached": len(self.embeddings_cache),
            "vector_index_size": self.memory_index.ntotal if self.memory_index else 0,
            "database_connected": self.SessionLocal is not None
        }

# Example usage and API endpoints
async def create_memory_endpoints(app):
    """Create FastAPI endpoints for memory system"""
    memory_system = BrainOpsMemorySystem()

    @app.post("/api/v1/memory/store")
    async def store_memory(
        content: str,
        memory_type: str = "semantic",
        importance: float = 0.5,
        metadata: Dict[str, Any] = None,
        tags: List[str] = None
    ):
        """Store a new memory"""
        memory = memory_system.store(
            content=content,
            memory_type=MemoryType(memory_type),
            importance=importance,
            metadata=metadata,
            tags=tags
        )
        return {
            "memory_id": memory.id,
            "strength": memory.calculate_strength()
        }

    @app.post("/api/v1/memory/recall")
    async def recall_memories(
        query: str,
        memory_types: List[str] = None,
        limit: int = 10,
        min_relevance: float = 0.3
    ):
        """Recall relevant memories"""
        types = [MemoryType(t) for t in memory_types] if memory_types else None
        memories = memory_system.recall(query, types, limit, min_relevance)

        return {
            "query": query,
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "relevance": float(r),
                    "type": m.memory_type.value,
                    "strength": m.calculate_strength()
                }
                for m, r in memories
            ]
        }

    @app.post("/api/v1/memory/reason")
    async def reason_with_memory(
        query: str,
        context: Dict[str, Any] = None
    ):
        """Multi-step reasoning with memory"""
        result = memory_system.reason(query, context)
        return result

    @app.get("/api/v1/memory/stats")
    async def get_memory_stats():
        """Get memory system statistics"""
        return memory_system.get_stats()

    @app.post("/api/v1/memory/forget")
    async def forget_irrelevant_memories(threshold: float = 0.1):
        """Forget irrelevant memories"""
        forgotten = memory_system.forget_irrelevant(threshold)
        return {
            "forgotten_count": len(forgotten),
            "forgotten_ids": forgotten
        }

    return memory_system

if __name__ == "__main__":
    # Test the memory system
    memory = BrainOpsMemorySystem()

    # Store some memories
    m1 = memory.store(
        "The backend API is deployed on Render at https://brainops-backend-prod.onrender.com",
        MemoryType.SEMANTIC,
        ImportanceLevel.CRITICAL.value,
        tags=["deployment", "backend", "api"]
    )

    m2 = memory.store(
        "WeatherCraft ERP migration is 45% complete as of 2025-09-18",
        MemoryType.EPISODIC,
        ImportanceLevel.HIGH.value,
        tags=["weathercraft", "migration", "progress"]
    )

    # Recall memories
    results = memory.recall("What is the status of WeatherCraft?")
    for mem, relevance in results:
        print(f"Relevance {relevance:.2f}: {mem.content}")

    # Reason about a query
    reasoning = memory.reason("How do I deploy the backend?")
    print(json.dumps(reasoning, indent=2))

    # Get stats
    print(json.dumps(memory.get_stats(), indent=2))