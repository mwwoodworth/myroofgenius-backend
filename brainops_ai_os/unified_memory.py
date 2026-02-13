"""
BrainOps AI OS - Unified Memory Substrate

Consolidates all memory systems into one coherent substrate:
- Episodic Memory (specific events and experiences)
- Semantic Memory (facts and knowledge)
- Procedural Memory (skills and procedures)
- Working Memory (current context)
- Long-term Memory (persistent storage)

Provides:
- Vector embeddings for semantic search
- Memory consolidation and compression
- Importance-based retention
- Associative memory linking
- Memory decay and reinforcement
"""

import asyncio
import json
import logging
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
import asyncpg
import numpy as np

from ._resilience import ResilientSubsystem

if TYPE_CHECKING:
    from .metacognitive_controller import MetacognitiveController

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """Types of memory in the unified substrate"""

    EPISODIC = "episodic"  # Specific events
    SEMANTIC = "semantic"  # Facts and knowledge
    PROCEDURAL = "procedural"  # How to do things
    WORKING = "working"  # Current context
    LONG_TERM = "long_term"  # Persistent storage


class MemoryState(str, Enum):
    """States of memory items"""

    ACTIVE = "active"
    CONSOLIDATING = "consolidating"
    ARCHIVED = "archived"
    DECAYED = "decayed"


@dataclass
class Memory:
    """A memory unit in the substrate"""

    id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    embedding: Optional[List[float]] = None
    importance: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    associations: List[str] = field(default_factory=list)
    state: MemoryState = MemoryState.ACTIVE
    decay_rate: float = 0.01
    metadata: Dict[str, Any] = field(default_factory=dict)


class UnifiedMemorySubstrate(ResilientSubsystem):
    """
    Unified Memory Substrate for BrainOps AI OS

    Provides a single, coherent memory system that:
    1. Stores and retrieves memories with vector search
    2. Consolidates memories during low-activity periods
    3. Manages memory decay and reinforcement
    4. Links related memories through associations
    5. Compresses old memories while retaining essence
    """

    def __init__(self, controller: "MetacognitiveController"):
        self.controller = controller
        self.db_pool: Optional[asyncpg.Pool] = None

        # Working memory - fast access, limited size
        self.working_memory: Dict[str, Memory] = {}
        self.working_memory_limit = 100

        # Memory cache for frequently accessed items
        self.memory_cache: Dict[str, Memory] = {}
        self.cache_limit = 1000

        # Embedding model configuration
        self.embedding_dim = 1536  # OpenAI ada-002
        self._openai_client = None
        self._openai_key = os.getenv("OPENAI_API_KEY")

        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown = asyncio.Event()

        # Metrics
        self.metrics = {
            "total_memories": 0,
            "memories_stored": 0,
            "memories_recalled": 0,
            "cache_hits": 0,
            "consolidations": 0,
            "associations_created": 0,
        }

    async def initialize(self, db_pool: asyncpg.Pool):
        """Initialize the unified memory substrate"""
        self.db_pool = db_pool

        # Initialize OpenAI client for embeddings
        if self._openai_key:
            import openai

            self._openai_client = openai.AsyncOpenAI(api_key=self._openai_key)

        # Create database tables
        try:
            await self._initialize_database()
        except RuntimeError as e:
            if "BLOCKED_RUNTIME_DDL" in str(e):
                logger.info("DDL kill-switch active — skipping runtime table creation")
            else:
                raise
        except Exception as e:
            if "permission denied" in str(e).lower():
                pass
            else:
                raise

        # Load working memory
        await self._load_working_memory()

        # Start background processes
        await self._start_background_processes()

        # Get initial count
        count = await self._db_fetchval_with_retry(
            "SELECT COUNT(*) FROM unified_ai_memory WHERE archived = false"
        )
        self.metrics["total_memories"] = count or 0

        logger.info(
            f"UnifiedMemorySubstrate initialized with {self.metrics['total_memories']} memories"
        )

    async def _initialize_database(self):
        """V7: unified_ai_memory already exists via migration.
        DDL is blocked by the kill-switch in production/staging.
        This method only runs in dev with ENABLE_RUNTIME_DDL=1.
        """
        # Ensure vector extension
        await self._db_execute_with_retry("CREATE EXTENSION IF NOT EXISTS vector")

        # NOTE: unified_ai_memory (42-column canonical table) is managed by
        # migrations, NOT runtime DDL. The DDL kill-switch will block these
        # CREATE statements in production. They exist only for local dev.
        await self._db_execute_with_retry(
            """
            -- Memory consolidation log (supporting table)
            CREATE TABLE IF NOT EXISTS brainops_memory_consolidation (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                memories_processed INT NOT NULL,
                memories_archived INT DEFAULT 0,
                memories_compressed INT DEFAULT 0,
                associations_created INT DEFAULT 0,
                duration_seconds FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            );

            -- Knowledge synthesis results (supporting table)
            CREATE TABLE IF NOT EXISTS brainops_synthesized_knowledge (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                source_memories TEXT[] NOT NULL,
                synthesis TEXT NOT NULL,
                confidence FLOAT DEFAULT 0.5,
                embedding vector(1536),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """
        )

    async def _load_working_memory(self):
        """Load recent important memories into working memory"""
        rows = await self._db_fetch_with_retry(
            """
            SELECT id, memory_type, content, importance_score,
                   access_count, last_accessed, related_memories, metadata
            FROM unified_ai_memory
            WHERE archived = false
            ORDER BY last_accessed DESC NULLS LAST, importance_score DESC
            LIMIT $1
        """,
            self.working_memory_limit,
        )

        for row in rows:
            memory = Memory(
                id=str(row["id"]),
                memory_type=MemoryType(row["memory_type"]),
                content=row["content"],
                importance=row["importance_score"],
                access_count=row["access_count"],
                last_accessed=row["last_accessed"],
                associations=[str(r) for r in (row["related_memories"] or [])],
                metadata=row["metadata"] or {},
            )
            self.working_memory[memory.id] = memory

        logger.info(f"Loaded {len(self.working_memory)} memories into working memory")

    async def _start_background_processes(self):
        """Start background memory processes"""
        # Memory consolidation - runs during low activity
        self._tasks.append(
            self._create_safe_task(
                self._consolidation_loop(), name="memory_consolidation"
            )
        )

        # Memory decay processing
        self._tasks.append(
            self._create_safe_task(self._decay_loop(), name="memory_decay")
        )

        # Association strengthening
        self._tasks.append(
            self._create_safe_task(
                self._association_loop(), name="association_strengthening"
            )
        )

        # Working memory management
        self._tasks.append(
            self._create_safe_task(self._working_memory_loop(), name="working_memory")
        )

        logger.info(f"Started {len(self._tasks)} memory background processes")

    # =========================================================================
    # CORE MEMORY OPERATIONS
    # =========================================================================

    async def store(
        self,
        data: Dict[str, Any],
        importance: float = 0.5,
        memory_type: MemoryType = MemoryType.EPISODIC,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store data in unified memory.

        Args:
            data: The data to store
            importance: Importance score (0-1)
            memory_type: Type of memory
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        import uuid

        memory_id = str(uuid.uuid4())

        # Generate embedding
        embedding = await self._generate_embedding(json.dumps(data))

        # Create memory object
        memory = Memory(
            id=memory_id,
            memory_type=memory_type,
            content=data,
            embedding=embedding,
            importance=importance,
            metadata=metadata or {},
        )

        # Store in database
        embedding_str = self._embedding_to_string(embedding) if embedding else None

        await self._db_execute_with_retry(
            """
            INSERT INTO unified_ai_memory
            (id, memory_type, content, embedding, importance_score, metadata,
             source_system, created_by)
            VALUES ($1::uuid, $2, $3, $4::vector, $5, $6,
                    'brainops_ai_os', 'unified_memory_substrate')
        """,
            memory_id,
            memory_type.value,
            json.dumps(data),
            embedding_str,
            importance,
            json.dumps(metadata or {}),
        )

        # Add to working memory if important enough
        if importance >= 0.5 or memory_type == MemoryType.WORKING:
            self.working_memory[memory_id] = memory
            await self._manage_working_memory_size()

        self.metrics["memories_stored"] += 1
        self.metrics["total_memories"] += 1

        # Find and create associations
        if embedding:
            await self._create_automatic_associations(memory_id, embedding)

        return memory_id

    async def recall(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None,
        min_importance: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Recall memories related to a query using semantic search.

        Args:
            query: Search query
            limit: Maximum results
            memory_type: Filter by memory type
            min_importance: Minimum importance threshold

        Returns:
            List of relevant memories
        """
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        if not query_embedding:
            return []

        embedding_str = self._embedding_to_string(query_embedding)

        # Search database
        type_filter = "AND memory_type = $4" if memory_type else ""
        type_param = [memory_type.value] if memory_type else []

        rows = await self._db_fetch_with_retry(
            f"""
            SELECT
                id, memory_type, content, importance_score,
                access_count, related_memories, metadata, created_at,
                1 - (embedding <=> $1::vector) as similarity
            FROM unified_ai_memory
            WHERE archived = false
            AND importance_score >= $3
            {type_filter}
            ORDER BY similarity DESC
            LIMIT $2
        """,
            embedding_str,
            limit,
            min_importance,
            *type_param,
        )

        memories = []
        for row in rows:
            memory = {
                "id": str(row["id"]),
                "type": row["memory_type"],
                "content": row["content"],
                "importance": row["importance_score"],
                "access_count": row["access_count"],
                "associations": [str(r) for r in (row["related_memories"] or [])],
                "metadata": row["metadata"] or {},
                "created_at": row["created_at"].isoformat()
                if row["created_at"]
                else None,
                "similarity": float(row["similarity"]),
            }
            memories.append(memory)

            # Update access statistics
            await self._db_execute_with_retry(
                """
                UPDATE unified_ai_memory
                SET access_count = access_count + 1,
                    last_accessed = NOW()
                WHERE id = $1::uuid
            """,
                str(row["id"]),
            )

        self.metrics["memories_recalled"] += len(memories)
        return memories

    async def recall_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Recall a specific memory by ID"""
        # Check working memory first
        if memory_id in self.working_memory:
            memory = self.working_memory[memory_id]
            self.metrics["cache_hits"] += 1
            return {
                "id": memory.id,
                "type": memory.memory_type.value,
                "content": memory.content,
                "importance": memory.importance,
                "access_count": memory.access_count,
            }

        # Check cache
        if memory_id in self.memory_cache:
            memory = self.memory_cache[memory_id]
            self.metrics["cache_hits"] += 1
            return {
                "id": memory.id,
                "type": memory.memory_type.value,
                "content": memory.content,
                "importance": memory.importance,
            }

        # Fetch from database
        row = await self._db_fetchrow_with_retry(
            """
            SELECT id, memory_type, content, importance_score,
                   access_count, related_memories, metadata, created_at
            FROM unified_ai_memory
            WHERE id = $1::uuid AND archived = false
        """,
            memory_id,
        )

        if row:
            # Update access
            await self._db_execute_with_retry(
                """
                UPDATE unified_ai_memory
                SET access_count = access_count + 1, last_accessed = NOW()
                WHERE id = $1::uuid
            """,
                memory_id,
            )

            return {
                "id": str(row["id"]),
                "type": row["memory_type"],
                "content": row["content"],
                "importance": row["importance_score"],
                "access_count": row["access_count"] + 1,
                "associations": [str(r) for r in (row["related_memories"] or [])],
                "metadata": row["metadata"] or {},
                "created_at": row["created_at"].isoformat()
                if row["created_at"]
                else None,
            }

        return None

    async def forget(self, memory_id: str, hard_delete: bool = False) -> bool:
        """
        Forget a memory (soft delete by default).

        Args:
            memory_id: Memory to forget
            hard_delete: If True, permanently delete

        Returns:
            True if successful
        """
        if hard_delete:
            result = await self._db_execute_with_retry(
                """
                DELETE FROM unified_ai_memory
                WHERE id = $1::uuid
            """,
                memory_id,
            )
        else:
            result = await self._db_execute_with_retry(
                """
                UPDATE unified_ai_memory
                SET archived = true, archived_at = NOW()
                WHERE id = $1::uuid
            """,
                memory_id,
            )

        # Remove from working memory and cache
        self.working_memory.pop(memory_id, None)
        self.memory_cache.pop(memory_id, None)

        return True

    async def reinforce(self, memory_id: str, strength: float = 0.1) -> bool:
        """
        Reinforce a memory, increasing its importance.

        Args:
            memory_id: Memory to reinforce
            strength: How much to increase importance

        Returns:
            True if successful
        """
        await self._db_execute_with_retry(
            """
            UPDATE unified_ai_memory
            SET importance_score = LEAST(importance_score + $2, 1.0),
                access_count = access_count + 1,
                last_accessed = NOW()
            WHERE id = $1::uuid
        """,
            memory_id,
            strength,
        )

        # Update in working memory if present
        if memory_id in self.working_memory:
            self.working_memory[memory_id].importance = min(
                self.working_memory[memory_id].importance + strength, 1.0
            )

        return True

    # =========================================================================
    # ASSOCIATION MANAGEMENT
    # =========================================================================

    async def create_association(
        self,
        source_id: str,
        target_id: str,
        association_type: str = "related",
        strength: float = 0.5,
    ) -> bool:
        """Create an association between two memories using related_memories array"""
        # Update related_memories array on the source memory
        await self._db_execute_with_retry(
            """
            UPDATE unified_ai_memory
            SET related_memories = array_append(
                COALESCE(related_memories, ARRAY[]::uuid[]),
                $2::uuid
            )
            WHERE id = $1::uuid
            AND NOT ($2::uuid = ANY(COALESCE(related_memories, ARRAY[]::uuid[])))
        """,
            source_id,
            target_id,
        )

        self.metrics["associations_created"] += 1
        return True

    async def _create_automatic_associations(
        self, memory_id: str, embedding: List[float]
    ):
        """Automatically create associations with similar memories"""
        embedding_str = self._embedding_to_string(embedding)

        # Find similar memories
        similar = await self._db_fetch_with_retry(
            """
            SELECT id,
                   1 - (embedding <=> $1::vector) as similarity
            FROM unified_ai_memory
            WHERE id != $2::uuid
            AND archived = false
            AND embedding IS NOT NULL
            ORDER BY similarity DESC
            LIMIT 5
        """,
            embedding_str,
            memory_id,
        )

        for row in similar:
            if row["similarity"] > 0.7:  # Only associate if similar enough
                await self.create_association(
                    memory_id,
                    str(row["id"]),
                    "semantic_similarity",
                    float(row["similarity"]),
                )

    async def get_associated_memories(
        self, memory_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get memories associated with a given memory via related_memories array"""
        rows = await self._db_fetch_with_retry(
            """
            SELECT m.id, m.memory_type, m.content, m.importance_score
            FROM unified_ai_memory src
            CROSS JOIN LATERAL unnest(src.related_memories) AS rel_id
            JOIN unified_ai_memory m ON m.id = rel_id
            WHERE src.id = $1::uuid
            AND m.archived = false
            LIMIT $2
        """,
            memory_id,
            limit,
        )

        return [
            {
                "id": str(row["id"]),
                "type": row["memory_type"],
                "content": row["content"],
                "importance": row["importance_score"],
                "association_type": "related",
                "strength": 1.0,
            }
            for row in rows
        ]

    # =========================================================================
    # BACKGROUND PROCESSES
    # =========================================================================

    async def _consolidation_loop(self):
        """Consolidate memories during low-activity periods"""
        while not self._shutdown.is_set():
            try:
                # Run consolidation every hour
                await asyncio.sleep(3600)

                logger.info("Starting memory consolidation...")
                start_time = datetime.now()

                # Consolidate similar memories
                consolidated = await self._consolidate_similar_memories()

                # Archive old low-importance memories
                archived = await self._archive_old_memories()

                # Log consolidation
                duration = (datetime.now() - start_time).total_seconds()
                await self._db_execute_with_retry(
                    """
                    INSERT INTO brainops_memory_consolidation
                    (memories_processed, memories_archived, duration_seconds)
                    VALUES ($1, $2, $3)
                """,
                    consolidated,
                    archived,
                    duration,
                )

                self.metrics["consolidations"] += 1
                logger.info(
                    f"Consolidation complete: {consolidated} processed, {archived} archived in {duration:.1f}s"
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consolidation error: {e}")
                await asyncio.sleep(3600)

    async def _consolidate_similar_memories(self) -> int:
        """Consolidate very similar memories into summaries"""
        processed = 0

        # Find clusters of similar memories
        # This is a simplified version - production would use proper clustering
        rows = await self._db_fetch_with_retry(
            """
            WITH memory_pairs AS (
                SELECT
                    m1.id::text as id1,
                    m2.id::text as id2,
                    1 - (m1.embedding <=> m2.embedding) as similarity
                FROM unified_ai_memory m1
                JOIN unified_ai_memory m2
                    ON m1.id < m2.id
                WHERE m1.state = 'active'
                AND m2.state = 'active'
                AND m1.embedding IS NOT NULL
                AND m2.embedding IS NOT NULL
                AND 1 - (m1.embedding <=> m2.embedding) > 0.95
            )
            SELECT id1, id2, similarity
            FROM memory_pairs
            LIMIT 100
        """
        )

        for row in rows:
            # Create association if very similar
            await self.create_association(
                row["id1"], row["id2"], "near_duplicate", row["similarity"]
            )
            processed += 1

        return processed

    async def _archive_old_memories(self) -> int:
        """Archive old, low-importance, rarely-accessed memories"""
        result = await self._db_execute_with_retry(
            """
            UPDATE unified_ai_memory
            SET archived = true, archived_at = NOW()
            WHERE archived = false
            AND importance_score < 0.3
            AND access_count < 3
            AND created_at < NOW() - INTERVAL '30 days'
            AND (last_accessed IS NULL OR last_accessed < NOW() - INTERVAL '14 days')
        """
        )

        # Parse affected rows
        try:
            archived = int(result.split()[-1])
        except:
            archived = 0

        return archived

    async def _decay_loop(self):
        """Apply memory decay over time"""
        while not self._shutdown.is_set():
            try:
                # Run decay every 6 hours
                await asyncio.sleep(21600)

                # Decay memories that haven't been accessed recently
                await self._db_execute_with_retry(
                    """
                    UPDATE unified_ai_memory
                    SET importance_score = GREATEST(importance_score * (1 - decay_rate), 0.1)
                    WHERE archived = false
                    AND last_accessed < NOW() - INTERVAL '7 days'
                    AND importance_score > 0.1
                """
                )

                logger.info("Memory decay applied")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Decay loop error: {e}")
                await asyncio.sleep(21600)

    async def _association_loop(self):
        """Strengthen associations based on co-access patterns"""
        while not self._shutdown.is_set():
            try:
                # Run every 30 minutes
                await asyncio.sleep(1800)

                # Find memories accessed together (within 5 minutes)
                # and strengthen their associations
                await self._db_execute_with_retry(
                    """
                    UPDATE unified_ai_memory dst
                    SET related_memories = array_append(dst.related_memories, src.id)
                    FROM unified_ai_memory src
                    WHERE dst.archived = false
                    AND src.archived = false
                    AND dst.id <> src.id
                    AND dst.last_accessed IS NOT NULL
                    AND src.last_accessed IS NOT NULL
                    AND ABS(EXTRACT(EPOCH FROM (dst.last_accessed - src.last_accessed))) < 300
                    AND NOT (dst.related_memories @> ARRAY[src.id])
                """
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Association loop error: {e}")
                await asyncio.sleep(1800)

    async def _working_memory_loop(self):
        """Manage working memory contents"""
        while not self._shutdown.is_set():
            try:
                # Run every minute
                await asyncio.sleep(60)

                await self._manage_working_memory_size()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Working memory loop error: {e}")
                await asyncio.sleep(60)

    async def _manage_working_memory_size(self):
        """Keep working memory within size limits"""
        if len(self.working_memory) > self.working_memory_limit:
            # Sort by importance and recency
            sorted_memories = sorted(
                self.working_memory.items(),
                key=lambda x: (x[1].importance, x[1].last_accessed or datetime.min),
                reverse=True,
            )

            # Keep top items
            self.working_memory = {
                k: v for k, v in sorted_memories[: self.working_memory_limit]
            }

    # =========================================================================
    # EMBEDDING GENERATION
    # =========================================================================

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        if not self._openai_client:
            return self._generate_fallback_embedding(text)

        try:
            # Truncate if too long
            truncated = text[:30000] if len(text) > 30000 else text

            response = await self._openai_client.embeddings.create(
                model="text-embedding-3-small", input=truncated
            )

            if response.data:
                return response.data[0].embedding

        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return self._generate_fallback_embedding(text)

        return None

    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate a deterministic fallback embedding from text hash"""
        # Use SHA-256 hash to generate deterministic embedding
        hash_bytes = hashlib.sha256(text.encode()).digest()

        # Extend to required dimension
        embedding = []
        for i in range(self.embedding_dim):
            byte_idx = i % len(hash_bytes)
            embedding.append((hash_bytes[byte_idx] / 255.0) - 0.5)

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = [x / norm for x in embedding]

        return embedding

    def _embedding_to_string(self, embedding: List[float]) -> str:
        """Convert embedding to PostgreSQL vector string"""
        return "[" + ",".join(str(x) for x in embedding) + "]"

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def process_memory_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a memory request from the controller"""
        action = request.get("action", "recall")

        if action == "store":
            memory_id = await self.store(
                request.get("data", {}),
                request.get("importance", 0.5),
                MemoryType(request.get("type", "episodic")),
                request.get("metadata"),
            )
            return {"status": "stored", "memory_id": memory_id}

        elif action == "recall":
            memories = await self.recall(
                request.get("query", ""),
                request.get("limit", 10),
                MemoryType(request.get("type")) if request.get("type") else None,
                request.get("min_importance", 0.0),
            )
            return {"status": "recalled", "memories": memories}

        elif action == "forget":
            success = await self.forget(
                request.get("memory_id"), request.get("hard_delete", False)
            )
            return {"status": "forgotten" if success else "failed"}

        elif action == "reinforce":
            success = await self.reinforce(
                request.get("memory_id"), request.get("strength", 0.1)
            )
            return {"status": "reinforced" if success else "failed"}

        return {"status": "unknown_action"}

    async def get_health(self) -> Dict[str, Any]:
        """Get memory system health"""
        active_tasks = sum(1 for t in self._tasks if not t.done())

        return {
            "status": "healthy" if active_tasks == len(self._tasks) else "degraded",
            "score": active_tasks / len(self._tasks) if self._tasks else 1.0,
            "working_memory_size": len(self.working_memory),
            "working_memory_limit": self.working_memory_limit,
            "cache_size": len(self.memory_cache),
            "metrics": self.metrics.copy(),
        }

    async def get_stats(self) -> Dict[str, int]:
        """Get memory statistics"""
        stats = await self._db_fetchrow_with_retry(
            """
            SELECT
                COUNT(*) FILTER (WHERE archived = false) as active,
                COUNT(*) FILTER (WHERE archived = true) as archived,
                COUNT(*) as total
            FROM unified_ai_memory
        """
        )

        return {
            "active": stats["active"] or 0,
            "archived": stats["archived"] or 0,
            "total": stats["total"] or 0,
            "working_memory": len(self.working_memory),
            "cache": len(self.memory_cache),
        }

    async def shutdown(self):
        """Shutdown the memory system"""
        self._shutdown.set()

        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("UnifiedMemorySubstrate shutdown complete")


# Singleton
_unified_memory: Optional[UnifiedMemorySubstrate] = None


def get_unified_memory() -> Optional[UnifiedMemorySubstrate]:
    """Get the unified memory instance"""
    return _unified_memory
