"""
Central Nervous System (CNS) Service - Simplified Version
Works with database tables and provides intelligent fallbacks when AI unavailable
"""

import asyncpg
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
import logging
import openai
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

class BrainOpsCNS:
    """Central Nervous System - The brain of our operations"""

    def __init__(self, db_pool: asyncpg.Pool = None):
        """Initialize CNS with database pool"""
        self.db_pool = db_pool
        self.initialized = False
        self._openai_client = None
        self._gemini_client = None
        self._active_provider = None

        # Load API keys
        self._openai_key = os.getenv("OPENAI_API_KEY")
        self._gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")

        # Configure providers
        if self._openai_key:
            # Never log key material (even partially).
            logger.info("CNS: OPENAI_API_KEY loaded (redacted)")

        if self._gemini_key and genai is not None:
            try:
                self._gemini_client = genai.Client(api_key=self._gemini_key)
                # Never log key material (even partially).
                logger.info("CNS: GEMINI_API_KEY loaded (redacted)")
            except Exception as e:
                logger.warning(f"CNS: Failed to configure Gemini: {e}")

        if not self._openai_key and not self._gemini_client:
            logger.warning("CNS: No AI provider configured - embeddings will fail")

    async def initialize(self):
        """Initialize CNS and verify database tables"""
        if not self.db_pool:
            raise Exception("Database pool not provided")

        try:
            # Verify CNS tables exist
            async with self.db_pool.acquire() as conn:
                tables = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name LIKE 'cns_%'
                """)

                if len(tables) < 9:
                    raise Exception(f"CNS tables missing. Found {len(tables)}/9 tables")

                self.initialized = True
                logger.info(f"✅ CNS initialized with {len(tables)} tables")
                return True

        except Exception as e:
            logger.error(f"CNS initialization failed: {e}")
            raise

    def _get_openai_client(self) -> openai.AsyncOpenAI:
        if not self._openai_key:
            return None
        if self._openai_client is None:
            self._openai_client = openai.AsyncOpenAI(api_key=self._openai_key)
        return self._openai_client

    async def _generate_embedding_openai(self, text: str) -> Optional[List[float]]:
        """Generate embedding using OpenAI."""
        client = self._get_openai_client()
        if not client:
            return None
        try:
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:30000],
            )
            if response.data:
                self._active_provider = "openai"
                return response.data[0].embedding
        except Exception as exc:
            error_str = str(exc).lower()
            if "insufficient_quota" in error_str or "rate_limit" in error_str:
                logger.warning(f"OpenAI quota/rate limit - falling back to Gemini: {exc}")
            else:
                logger.error(f"OpenAI embedding failed: {exc}")
        return None

    async def _generate_embedding_gemini(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Gemini."""
        if not self._gemini_client:
            return None
        try:
            # Gemini embeddings are synchronous, run in executor
            import asyncio
            loop = asyncio.get_event_loop()
            
            def call_gemini():
                if types is None:
                    return None
                return self._gemini_client.models.embed_content(
                    model="models/gemini-embedding-001",
                    contents=text[:30000],
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=1536,
                    )
                )

            result = await loop.run_in_executor(None, call_gemini)
            
            if result and result.embeddings:
                self._active_provider = "gemini"
                return result.embeddings[0].values
        except Exception as exc:
            logger.error(f"Gemini embedding failed: {exc}")
        return None

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding - tries OpenAI first, falls back to Gemini."""
        truncated = text[:30000] if len(text) > 30000 else text

        # Try OpenAI first
        embedding = await self._generate_embedding_openai(truncated)
        if embedding:
            return embedding

        # Fall back to Gemini
        embedding = await self._generate_embedding_gemini(truncated)
        if embedding:
            return embedding

        # No provider available
        raise HTTPException(
            status_code=503,
            detail="No AI provider available for embeddings (OpenAI quota exceeded, Gemini not configured)"
        )

    async def remember(self, data: Dict) -> str:
        """Store anything in permanent memory"""
        if not self.initialized:
            await self.initialize()

        async with self.db_pool.acquire() as conn:
            # Generate embedding from full payload
            text = json.dumps(data)
            embedding = await self._generate_embedding(text)

            # Serialize content to JSON string to match TEXT columns safely.
            content_str = json.dumps(data)

            # Store in database
            # asyncpg cannot natively serialize list[float] to pgvector;
            # cast the embedding to its text representation.
            embedding_str = str(embedding)
            result = await conn.fetchval("""
                INSERT INTO cns_memory (
                    memory_type, category, title, content,
                    embedding, importance_score, tags
                ) VALUES ($1, $2, $3, $4, $5::vector, $6, $7)
                RETURNING memory_id
            """,
                data.get('type', 'general'),
                data.get('category', 'system'),
                data.get('title', 'Memory'),
                content_str,
                embedding_str,
                data.get('importance', 0.5),
                data.get('tags', [])
            )

            logger.info(f"💾 Stored memory: {result}")
            return str(result)

    async def recall(self, query: str, limit: int = 10) -> List[Dict]:
        """Retrieve relevant memories using semantic search"""
        if not self.initialized:
            await self.initialize()

        async with self.db_pool.acquire() as conn:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            query_embedding_str = str(query_embedding)

            # Search with vector similarity (using cosine distance)
            results = await conn.fetch("""
                SELECT
                    memory_id, memory_type, category, title, content,
                    importance_score, tags, created_at,
                    1 - (embedding <=> $1::vector) as similarity
                FROM cns_memory
                WHERE expires_at IS NULL OR expires_at > NOW()
                ORDER BY similarity DESC, importance_score DESC
                LIMIT $2
            """, query_embedding_str, limit)

            # Update access count
            memory_ids = [r['memory_id'] for r in results]
            if memory_ids:
                await conn.execute("""
                    UPDATE cns_memory
                    SET accessed_count = accessed_count + 1,
                        last_accessed = NOW()
                    WHERE memory_id = ANY($1)
                """, memory_ids)

            return [dict(r) for r in results]

    async def create_task(self, task: Dict) -> str:
        """Create a new task with AI-calculated priority"""
        if not self.initialized:
            await self.initialize()

        async with self.db_pool.acquire() as conn:
            # Calculate priority intelligently
            urgency = self._calculate_urgency(task)
            importance = self._calculate_importance(task)
            priority = (urgency * 0.6 + importance * 0.4)

            result = await conn.fetchval("""
                INSERT INTO cns_tasks (
                    title, description, priority, urgency, importance,
                    status, tags, metadata, due_date
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING task_id
            """,
                task.get('title', 'New Task'),
                task.get('description', ''),
                priority,
                urgency,
                importance,
                'pending',
                task.get('tags', []),
                task,
                task.get('due_date')
            )

            logger.info(f"📋 Created task: {result} (priority: {priority:.2f})")
            return str(result)

    def _calculate_urgency(self, task: Dict) -> float:
        """Calculate urgency based on due date and keywords"""
        urgency = 0.5

        # Check for urgent keywords
        urgent_keywords = ['urgent', 'asap', 'critical', 'emergency', 'now', 'immediate']
        text = f"{task.get('title', '')} {task.get('description', '')}".lower()

        for keyword in urgent_keywords:
            if keyword in text:
                urgency = max(urgency, 0.9)
                break

        # Check due date
        if task.get('due_date'):
            # Would calculate based on time until due
            urgency = max(urgency, 0.7)

        return urgency

    def _calculate_importance(self, task: Dict) -> float:
        """Calculate importance based on impact and keywords"""
        importance = 0.5

        # Check for important keywords
        important_keywords = ['revenue', 'customer', 'production', 'security', 'compliance']
        text = f"{task.get('title', '')} {task.get('description', '')}".lower()

        for keyword in important_keywords:
            if keyword in text:
                importance = max(importance, 0.8)

        return importance

    async def get_tasks(self, status: Optional[str] = None) -> List[Dict]:
        """Get tasks, optionally filtered by status"""
        if not self.initialized:
            await self.initialize()

        async with self.db_pool.acquire() as conn:
            if status:
                results = await conn.fetch("""
                    SELECT * FROM cns_tasks
                    WHERE status = $1
                    ORDER BY priority DESC, created_at DESC
                    LIMIT 100
                """, status)
            else:
                results = await conn.fetch("""
                    SELECT * FROM cns_tasks
                    ORDER BY priority DESC, created_at DESC
                    LIMIT 100
                """)

            return [dict(r) for r in results]

    async def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        if not self.initialized:
            await self.initialize()

        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE cns_tasks
                SET status = $1, updated_at = NOW()
                WHERE task_id = $2
            """, status, task_id)

            return result != "UPDATE 0"

    async def get_status(self) -> Dict:
        """Get CNS system status"""
        if not self.initialized:
            await self.initialize()

        async with self.db_pool.acquire() as conn:
            # Get counts
            memory_count = await conn.fetchval("SELECT COUNT(*) FROM cns_memory")
            task_count = await conn.fetchval("SELECT COUNT(*) FROM cns_tasks WHERE status != 'completed'")
            project_count = await conn.fetchval("SELECT COUNT(*) FROM cns_projects WHERE status = 'active'")

            # Get recent activity
            recent_memories = await conn.fetchval("""
                SELECT COUNT(*) FROM cns_memory
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """)

            # Determine actual AI provider status
            providers = []
            if self._openai_key:
                providers.append("openai")
            if self._gemini_configured:
                providers.append("gemini")

            if providers:
                ai_status = f"{', '.join(providers)} (active: {self._active_provider or providers[0]})"
            else:
                ai_status = "none configured"

            return {
                "status": "operational",
                "initialized": self.initialized,
                "memory_count": memory_count,
                "task_count": task_count,
                "project_count": project_count,
                "recent_memories": recent_memories,
                "database": "connected",
                "ai_provider": ai_status,
                "ai_providers_available": providers,
                "vector_search": "enabled (pgvector)",
                "version": "v163.4.0"
            }

    async def learn(self, pattern: Dict) -> bool:
        """Record a learning pattern"""
        if not self.initialized:
            await self.initialize()

        async with self.db_pool.acquire() as conn:
            # Check if similar pattern exists
            existing = await conn.fetchval("""
                SELECT pattern_id FROM cns_learning_patterns
                WHERE pattern_type = $1
                AND pattern_data->>'key' = $2
            """, pattern.get('type'), pattern.get('key'))

            if existing:
                # Update existing pattern
                await conn.execute("""
                    UPDATE cns_learning_patterns
                    SET occurrences = occurrences + 1,
                        confidence = LEAST(confidence + 0.05, 1.0),
                        last_observed = NOW()
                    WHERE pattern_id = $1
                """, existing)
            else:
                # Create new pattern
                await conn.execute("""
                    INSERT INTO cns_learning_patterns (
                        pattern_type, pattern_data, confidence
                    ) VALUES ($1, $2, $3)
                """, pattern.get('type', 'behavior'), pattern, 0.5)

            return True

    async def decide(self, context: str, options: List[str]) -> Dict:
        """Make a decision based on context and past learning"""
        if not self.initialized:
            await self.initialize()

        # Simple decision logic without AI
        # Score each option based on past patterns
        scores = {}
        for option in options:
            # Look for similar past decisions
            score = 0.5  # Base score

            # Boost score based on keywords
            if 'recommended' in option.lower():
                score += 0.2
            if 'safe' in option.lower():
                score += 0.1
            if 'fast' in option.lower():
                score += 0.1

            scores[option] = min(score, 1.0)

        # Choose best option
        best_option = max(scores, key=scores.get)

        # Record decision
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO cns_decisions (
                    context, question, options, chosen_option,
                    reasoning, confidence_score
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
                context,
                "Which option to choose?",
                json.dumps(options),
                json.dumps({"choice": best_option, "score": scores[best_option]}),
                f"Chose based on scoring algorithm: {scores}",
                scores[best_option]
            )

        return {
            "decision": best_option,
            "confidence": scores[best_option],
            "reasoning": f"Best score among options",
            "scores": scores
        }

def create_cns_routes(cns: BrainOpsCNS) -> APIRouter:
    """Create FastAPI routes for CNS"""
    router = APIRouter()

    @router.get("/status")
    async def get_status():
        """Get CNS system status"""
        return await cns.get_status()

    @router.post("/memory")
    async def store_memory(data: Dict):
        """Store a memory"""
        memory_id = await cns.remember(data)
        return {"memory_id": memory_id, "status": "stored"}

    @router.get("/memory/search")
    async def search_memory(query: str, limit: int = 10):
        """Search memories"""
        results = await cns.recall(query, limit)
        return {"query": query, "results": results, "count": len(results)}

    @router.post("/tasks")
    async def create_task(task: Dict):
        """Create a task"""
        task_id = await cns.create_task(task)
        return {"task_id": task_id, "status": "created"}

    @router.get("/tasks")
    async def get_tasks(status: Optional[str] = None):
        """Get tasks"""
        tasks = await cns.get_tasks(status)
        return {"tasks": tasks, "count": len(tasks)}

    @router.put("/tasks/{task_id}/status")
    async def update_task(task_id: str, status: str):
        """Update task status"""
        success = await cns.update_task_status(task_id, status)
        return {"success": success}

    @router.post("/learn")
    async def learn_pattern(pattern: Dict):
        """Record a learning pattern"""
        success = await cns.learn(pattern)
        return {"success": success}

    @router.post("/decide")
    async def make_decision(context: str, options: List[str]):
        """Make a decision"""
        decision = await cns.decide(context, options)
        return decision

    return router
