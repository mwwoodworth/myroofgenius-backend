"""
Persistent Memory Brain - The Real Living Memory System
This actively reads from and writes to Supabase continuously
"""

import os
import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from supabase import create_client, Client
import asyncpg
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

# Initialize connections
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PersistentMemoryBrain:
    """
    The actual brain that continuously uses Supabase as its memory
    Every thought, decision, and learning is stored and retrieved
    """
    
    def __init__(self):
        self.supabase = supabase
        self.memory_cache = {}  # Local cache for speed
        self.thought_stream = []  # Current thought stream
        self.learning_queue = []  # Queue of things to learn
        self.decision_history = []  # Recent decisions
        
        # Initialize memory tables
        asyncio.create_task(self._initialize_brain())
        
        # Start continuous memory processes
        asyncio.create_task(self._continuous_thinking())
        asyncio.create_task(self._memory_consolidation())
        asyncio.create_task(self._pattern_recognition())
        asyncio.create_task(self._knowledge_synthesis())
    
    async def _initialize_brain(self):
        """Initialize the brain's memory structure in Supabase"""
        try:
            # Create comprehensive memory tables
            conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
            
            # Core memory table - stores everything
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS brain_memory (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    memory_type VARCHAR(50),  -- thought, decision, knowledge, pattern, etc.
                    category VARCHAR(100),    -- business, technical, customer, etc.
                    content JSONB NOT NULL,    -- The actual memory
                    associations JSONB,        -- Links to other memories
                    embedding vector(1536),    -- For semantic search
                    importance FLOAT DEFAULT 0.5,
                    confidence FLOAT DEFAULT 0.8,
                    access_count INT DEFAULT 0,
                    decay_factor FLOAT DEFAULT 1.0,  -- Memory decay over time
                    reinforcement_count INT DEFAULT 0,  -- How many times reinforced
                    source VARCHAR(255),       -- Where this came from
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_accessed TIMESTAMP DEFAULT NOW(),
                    last_modified TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_memory_type ON brain_memory(memory_type);
                CREATE INDEX IF NOT EXISTS idx_memory_category ON brain_memory(category);
                CREATE INDEX IF NOT EXISTS idx_memory_importance ON brain_memory(importance DESC);
                CREATE INDEX IF NOT EXISTS idx_memory_embedding ON brain_memory USING ivfflat (embedding vector_cosine_ops);
            ''')
            
            # Thought stream - continuous thoughts
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS thought_stream (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    thought JSONB NOT NULL,
                    context JSONB,
                    triggered_by VARCHAR(255),
                    led_to VARCHAR(255),
                    quality_score FLOAT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            ''')
            
            # Decision log - every decision made
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS decision_log (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    decision_type VARCHAR(100),
                    input_context JSONB,
                    options_considered JSONB,
                    decision_made JSONB,
                    reasoning TEXT,
                    confidence FLOAT,
                    outcome JSONB,
                    success BOOLEAN,
                    learned_lesson JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            ''')
            
            # Pattern library - recognized patterns
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS pattern_library (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    pattern_name VARCHAR(255),
                    pattern_type VARCHAR(100),
                    pattern_data JSONB,
                    occurrences INT DEFAULT 1,
                    success_rate FLOAT,
                    last_seen TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW()
                );
            ''')
            
            # Knowledge synthesis - combined knowledge
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_synthesis (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    topic VARCHAR(255),
                    synthesized_knowledge JSONB,
                    source_memories JSONB,  -- IDs of memories that contributed
                    confidence FLOAT,
                    validation_status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            ''')
            
            # System state tracking
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS system_state (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    component VARCHAR(100),
                    state JSONB,
                    health_score FLOAT,
                    metrics JSONB,
                    anomalies JSONB,
                    timestamp TIMESTAMP DEFAULT NOW()
                );
            ''')
            
            # Learning objectives
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS learning_objectives (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    objective VARCHAR(255),
                    current_knowledge JSONB,
                    target_knowledge JSONB,
                    progress FLOAT DEFAULT 0,
                    priority INT DEFAULT 5,
                    deadline TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP
                );
            ''')
            
            await conn.close()
            
            # Log initialization
            await self.store_thought({
                "type": "initialization",
                "content": "Brain initialized with persistent memory",
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info("Brain memory structure initialized in Supabase")
            
        except Exception as e:
            logger.error(f"Failed to initialize brain: {e}")
    
    async def store_thought(self, thought: Dict, importance: float = 0.5):
        """Store a thought in persistent memory"""
        try:
            # Generate embedding for semantic search
            embedding = await self._generate_embedding(json.dumps(thought))
            
            # Store in brain memory
            result = self.supabase.table("brain_memory").insert({
                "memory_type": "thought",
                "category": thought.get("category", "general"),
                "content": thought,
                "importance": importance,
                "embedding": embedding,
                "source": thought.get("source", "internal")
            }).execute()
            
            # Also store in thought stream for continuity
            self.supabase.table("thought_stream").insert({
                "thought": thought,
                "context": {"memory_id": result.data[0]["id"] if result.data else None},
                "triggered_by": thought.get("triggered_by"),
                "quality_score": importance
            }).execute()
            
            # Update local cache
            if result.data:
                memory_id = result.data[0]["id"]
                self.memory_cache[memory_id] = thought
                
            # Add to thought stream
            self.thought_stream.append(thought)
            if len(self.thought_stream) > 100:
                self.thought_stream.pop(0)  # Keep last 100 thoughts
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to store thought: {e}")
            return None
    
    async def recall_memory(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Recall memories related to a query"""
        try:
            # Generate embedding for query
            query_embedding = await self._generate_embedding(query)
            
            # Search in Supabase using vector similarity
            # First, try semantic search
            memories = []
            
            # Text search as fallback (Supabase doesn't support vector ops in Python client yet)
            query_filter = self.supabase.table("brain_memory").select("*")
            
            if category:
                query_filter = query_filter.filter("category", "eq", category)
            
            # Search in content
            result = query_filter.filter(
                "content", "cs", json.dumps({"search": query})
            ).order("importance", desc=True).limit(limit).execute()
            
            if result.data:
                memories.extend(result.data)
                
                # Update access count and last accessed
                for memory in result.data:
                    self.supabase.table("brain_memory").update({
                        "access_count": memory["access_count"] + 1,
                        "last_accessed": datetime.now().isoformat()
                    }).eq("id", memory["id"]).execute()
            
            # If no results, try broader search
            if not memories:
                result = self.supabase.table("brain_memory").select("*").order(
                    "importance", desc=True
                ).limit(limit).execute()
                
                if result.data:
                    memories = result.data
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to recall memory: {e}")
            return []
    
    async def make_decision(self, context: Dict, options: List[Dict]) -> Dict:
        """Make a decision based on memory and context"""
        try:
            # Recall relevant memories
            relevant_memories = await self.recall_memory(
                json.dumps(context),
                category=context.get("category", "decision")
            )
            
            # Analyze options based on past decisions
            past_decisions = self.supabase.table("decision_log").select("*").filter(
                "decision_type", "eq", context.get("type", "general")
            ).filter("success", "eq", True).limit(10).execute()
            
            # Score each option
            option_scores = []
            for option in options:
                score = await self._score_option(option, relevant_memories, past_decisions.data)
                option_scores.append((option, score))
            
            # Sort by score
            option_scores.sort(key=lambda x: x[1], reverse=True)
            best_option = option_scores[0][0] if option_scores else options[0]
            
            # Create decision
            decision = {
                "decision_type": context.get("type", "general"),
                "input_context": context,
                "options_considered": options,
                "decision_made": best_option,
                "reasoning": f"Based on {len(relevant_memories)} relevant memories and {len(past_decisions.data) if past_decisions.data else 0} past successes",
                "confidence": option_scores[0][1] if option_scores else 0.5,
                "created_at": datetime.now().isoformat()
            }
            
            # Store decision
            result = self.supabase.table("decision_log").insert(decision).execute()
            
            # Store in brain memory
            await self.store_thought({
                "type": "decision",
                "content": decision,
                "category": "decision",
                "importance": 0.7
            })
            
            # Add to decision history
            self.decision_history.append(decision)
            if len(self.decision_history) > 50:
                self.decision_history.pop(0)
            
            return decision
            
        except Exception as e:
            logger.error(f"Failed to make decision: {e}")
            return {"error": str(e)}
    
    async def learn_from_outcome(self, decision_id: str, outcome: Dict, success: bool):
        """Learn from the outcome of a decision"""
        try:
            # Update decision with outcome
            self.supabase.table("decision_log").update({
                "outcome": outcome,
                "success": success,
                "learned_lesson": {
                    "what_worked": outcome.get("positives", []),
                    "what_failed": outcome.get("negatives", []),
                    "improvement": outcome.get("improvement", "")
                }
            }).eq("id", decision_id).execute()
            
            # Store learning as memory
            await self.store_thought({
                "type": "learning",
                "content": {
                    "decision_id": decision_id,
                    "outcome": outcome,
                    "success": success
                },
                "category": "learning",
                "importance": 0.8 if success else 0.9  # Learn more from failures
            })
            
            # If successful, reinforce the pattern
            if success:
                await self._reinforce_pattern(decision_id)
            else:
                await self._learn_from_failure(decision_id, outcome)
            
        except Exception as e:
            logger.error(f"Failed to learn from outcome: {e}")
    
    async def _reinforce_pattern(self, decision_id: str):
        """Reinforce successful patterns"""
        # Get the decision
        result = self.supabase.table("decision_log").select("*").eq("id", decision_id).execute()
        
        if result.data:
            decision = result.data[0]
            
            # Store as pattern
            self.supabase.table("pattern_library").insert({
                "pattern_name": f"success_{decision['decision_type']}",
                "pattern_type": "success",
                "pattern_data": {
                    "context": decision["input_context"],
                    "decision": decision["decision_made"]
                },
                "success_rate": 1.0
            }).execute()
            
            # Increase importance of related memories
            related_memories = await self.recall_memory(
                json.dumps(decision["input_context"]),
                limit=5
            )
            
            for memory in related_memories:
                self.supabase.table("brain_memory").update({
                    "importance": min(memory["importance"] + 0.1, 1.0),
                    "reinforcement_count": memory["reinforcement_count"] + 1
                }).eq("id", memory["id"]).execute()
    
    async def _learn_from_failure(self, decision_id: str, outcome: Dict):
        """Learn from failures to avoid them"""
        # Get the decision
        result = self.supabase.table("decision_log").select("*").eq("id", decision_id).execute()
        
        if result.data:
            decision = result.data[0]
            
            # Store as anti-pattern
            self.supabase.table("pattern_library").insert({
                "pattern_name": f"failure_{decision['decision_type']}",
                "pattern_type": "failure",
                "pattern_data": {
                    "context": decision["input_context"],
                    "decision": decision["decision_made"],
                    "failure_reason": outcome.get("reason", "unknown")
                },
                "success_rate": 0.0
            }).execute()
            
            # Create learning objective
            self.supabase.table("learning_objectives").insert({
                "objective": f"Improve {decision['decision_type']} decisions",
                "current_knowledge": {"failure": outcome},
                "target_knowledge": {"avoid": decision["decision_made"]},
                "priority": 8
            }).execute()
    
    async def synthesize_knowledge(self, topic: str) -> Dict:
        """Synthesize knowledge about a topic from all memories"""
        try:
            # Get all relevant memories
            memories = await self.recall_memory(topic, limit=50)
            
            # Get related patterns
            patterns = self.supabase.table("pattern_library").select("*").filter(
                "pattern_data", "cs", json.dumps({"topic": topic})
            ).execute()
            
            # Get related decisions
            decisions = self.supabase.table("decision_log").select("*").filter(
                "input_context", "cs", json.dumps({"topic": topic})
            ).execute()
            
            # Synthesize
            synthesis = {
                "topic": topic,
                "total_memories": len(memories),
                "patterns_found": len(patterns.data) if patterns.data else 0,
                "decisions_made": len(decisions.data) if decisions.data else 0,
                "key_insights": [],
                "confidence": 0.7,
                "timestamp": datetime.now().isoformat()
            }
            
            # Extract key insights
            if memories:
                # Group by importance
                important_memories = [m for m in memories if m["importance"] > 0.7]
                synthesis["key_insights"] = [m["content"] for m in important_memories[:5]]
                synthesis["confidence"] = np.mean([m["confidence"] for m in memories])
            
            # Store synthesis
            result = self.supabase.table("knowledge_synthesis").insert({
                "topic": topic,
                "synthesized_knowledge": synthesis,
                "source_memories": [m["id"] for m in memories],
                "confidence": synthesis["confidence"]
            }).execute()
            
            return synthesis
            
        except Exception as e:
            logger.error(f"Failed to synthesize knowledge: {e}")
            return {"error": str(e)}
    
    async def _continuous_thinking(self):
        """Continuous background thinking process"""
        while True:
            try:
                # Get current system state
                state = await self._get_system_state()
                
                # Generate thoughts about current state
                thought = {
                    "type": "observation",
                    "content": {
                        "system_health": state.get("health", "unknown"),
                        "active_processes": state.get("processes", []),
                        "concerns": state.get("concerns", [])
                    },
                    "category": "system_monitoring",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Store thought
                await self.store_thought(thought, importance=0.3)
                
                # Check for patterns
                if len(self.thought_stream) > 10:
                    patterns = await self._identify_thought_patterns()
                    if patterns:
                        await self.store_thought({
                            "type": "pattern_recognition",
                            "content": patterns,
                            "category": "meta_cognition"
                        }, importance=0.6)
                
                await asyncio.sleep(30)  # Think every 30 seconds
                
            except Exception as e:
                logger.error(f"Thinking error: {e}")
                await asyncio.sleep(60)
    
    async def _memory_consolidation(self):
        """Consolidate and organize memories"""
        while True:
            try:
                # Get memories that haven't been accessed recently
                old_memories = self.supabase.table("brain_memory").select("*").filter(
                    "last_accessed", "lt", (datetime.now() - timedelta(days=7)).isoformat()
                ).filter("importance", "lt", 0.5).limit(100).execute()
                
                if old_memories.data:
                    # Decay unimportant memories
                    for memory in old_memories.data:
                        new_importance = memory["importance"] * 0.95
                        if new_importance < 0.1:
                            # Archive or delete
                            self.supabase.table("brain_memory").delete().eq("id", memory["id"]).execute()
                        else:
                            self.supabase.table("brain_memory").update({
                                "importance": new_importance,
                                "decay_factor": memory["decay_factor"] * 0.98
                            }).eq("id", memory["id"]).execute()
                
                # Consolidate similar memories
                await self._consolidate_similar_memories()
                
                await asyncio.sleep(3600)  # Every hour
                
            except Exception as e:
                logger.error(f"Memory consolidation error: {e}")
                await asyncio.sleep(3600)
    
    async def _pattern_recognition(self):
        """Recognize patterns in memories and decisions"""
        while True:
            try:
                # Get recent decisions
                recent_decisions = self.supabase.table("decision_log").select("*").filter(
                    "created_at", "gte", (datetime.now() - timedelta(hours=24)).isoformat()
                ).execute()
                
                if recent_decisions.data:
                    # Group by type
                    decision_types = {}
                    for decision in recent_decisions.data:
                        dtype = decision["decision_type"]
                        if dtype not in decision_types:
                            decision_types[dtype] = []
                        decision_types[dtype].append(decision)
                    
                    # Find patterns in each type
                    for dtype, decisions in decision_types.items():
                        if len(decisions) > 3:
                            # Calculate success rate
                            success_rate = sum(1 for d in decisions if d.get("success")) / len(decisions)
                            
                            # Store pattern
                            self.supabase.table("pattern_library").insert({
                                "pattern_name": f"decision_pattern_{dtype}",
                                "pattern_type": "decision",
                                "pattern_data": {
                                    "type": dtype,
                                    "sample_size": len(decisions),
                                    "success_rate": success_rate
                                },
                                "occurrences": len(decisions),
                                "success_rate": success_rate
                            }).execute()
                
                await asyncio.sleep(600)  # Every 10 minutes
                
            except Exception as e:
                logger.error(f"Pattern recognition error: {e}")
                await asyncio.sleep(600)
    
    async def _knowledge_synthesis(self):
        """Synthesize knowledge from accumulated memories"""
        while True:
            try:
                # Get learning objectives
                objectives = self.supabase.table("learning_objectives").select("*").filter(
                    "progress", "lt", 1.0
                ).order("priority", desc=True).limit(5).execute()
                
                if objectives.data:
                    for objective in objectives.data:
                        # Synthesize knowledge for this objective
                        synthesis = await self.synthesize_knowledge(objective["objective"])
                        
                        # Update progress
                        progress = min(synthesis.get("confidence", 0) * 1.2, 1.0)
                        self.supabase.table("learning_objectives").update({
                            "progress": progress,
                            "current_knowledge": synthesis
                        }).eq("id", objective["id"]).execute()
                        
                        if progress >= 1.0:
                            # Mark as completed
                            self.supabase.table("learning_objectives").update({
                                "completed_at": datetime.now().isoformat()
                            }).eq("id", objective["id"]).execute()
                
                await asyncio.sleep(900)  # Every 15 minutes
                
            except Exception as e:
                logger.error(f"Knowledge synthesis error: {e}")
                await asyncio.sleep(900)
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            response = openai_client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except:
            # Return zero vector as fallback
            return [0.0] * 1536
    
    async def _score_option(self, option: Dict, memories: List[Dict], past_decisions: List[Dict]) -> float:
        """Score an option based on memories and past decisions"""
        score = 0.5  # Base score
        
        # Check if similar option worked before
        for decision in past_decisions:
            if decision.get("decision_made") == option:
                if decision.get("success"):
                    score += 0.2
                else:
                    score -= 0.2
        
        # Check memory importance
        if memories:
            avg_importance = np.mean([m["importance"] for m in memories])
            score += avg_importance * 0.3
        
        return min(max(score, 0), 1)  # Clamp between 0 and 1
    
    async def _identify_thought_patterns(self) -> List[Dict]:
        """Identify patterns in recent thoughts"""
        patterns = []
        
        # Look for repeated themes
        themes = {}
        for thought in self.thought_stream[-20:]:
            if isinstance(thought, dict):
                theme = thought.get("category", "unknown")
                themes[theme] = themes.get(theme, 0) + 1
        
        # Identify dominant themes
        for theme, count in themes.items():
            if count > 3:
                patterns.append({
                    "pattern": "repeated_theme",
                    "theme": theme,
                    "frequency": count
                })
        
        return patterns
    
    async def _consolidate_similar_memories(self):
        """Consolidate similar memories to save space"""
        # This would use embeddings to find similar memories
        # For now, simple implementation
        pass
    
    async def _get_system_state(self) -> Dict:
        """Get current system state"""
        # Query system state from database
        result = self.supabase.table("system_state").select("*").order(
            "timestamp", desc=True
        ).limit(1).execute()
        
        if result.data:
            return result.data[0]["state"]
        return {}
    
    async def get_brain_status(self) -> Dict:
        """Get current brain status"""
        # Get memory stats
        memory_count = self.supabase.table("brain_memory").select("count", count="exact").execute()
        thought_count = self.supabase.table("thought_stream").select("count", count="exact").execute()
        decision_count = self.supabase.table("decision_log").select("count", count="exact").execute()
        pattern_count = self.supabase.table("pattern_library").select("count", count="exact").execute()
        
        return {
            "total_memories": memory_count.count if memory_count else 0,
            "total_thoughts": thought_count.count if thought_count else 0,
            "total_decisions": decision_count.count if decision_count else 0,
            "recognized_patterns": pattern_count.count if pattern_count else 0,
            "current_thought_stream": len(self.thought_stream),
            "cached_memories": len(self.memory_cache),
            "recent_decisions": len(self.decision_history),
            "status": "active"
        }

# Global brain instance
brain = None

def get_brain() -> PersistentMemoryBrain:
    """Get the singleton brain instance"""
    global brain
    if brain is None:
        brain = PersistentMemoryBrain()
    return brain