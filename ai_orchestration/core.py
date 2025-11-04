"""
AI Orchestration Core - The Brain of the System
This is where true intelligence begins.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

import asyncpg
from pydantic import BaseModel
import httpx

# Supabase connection
DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent operational status"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    COMMUNICATING = "communicating"
    LEARNING = "learning"
    ERROR = "error"
    OFFLINE = "offline"

class MemoryType(Enum):
    """Types of agent memory"""
    KNOWLEDGE = "knowledge"  # Facts about the system
    EXPERIENCE = "experience"  # Past actions and outcomes
    ERROR = "error"  # Errors encountered and solutions
    SOLUTION = "solution"  # Successful fixes
    PATTERN = "pattern"  # Identified patterns
    INSIGHT = "insight"  # Derived understanding

class MessageType(Enum):
    """Inter-agent communication types"""
    QUERY = "query"  # Asking for information
    RESPONSE = "response"  # Answering a query
    ALERT = "alert"  # Urgent notification
    UPDATE = "update"  # Status update
    REQUEST = "request"  # Requesting action
    REPORT = "report"  # Reporting results

class SystemComponent(Enum):
    """System components to monitor"""
    BACKEND = "backend"
    FRONTEND_MRG = "frontend_mrg"
    FRONTEND_WC = "frontend_wc"
    DATABASE = "database"
    DEPLOYMENT = "deployment"
    AI_MODELS = "ai_models"
    MONITORING = "monitoring"

class AgentMemory:
    """Persistent memory for agents using Supabase"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.pool = None
        
    async def connect(self):
        """Connect to Supabase"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    
    async def remember(self, memory_type: MemoryType, content: Dict[str, Any], relevance: float = 1.0):
        """Store a memory"""
        await self.connect()
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO agent_memory (memory_id, agent_id, memory_type, content, relevance_score, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $6)
            """, str(uuid.uuid4()), self.agent_id, memory_type.value, json.dumps(content), relevance, datetime.utcnow())
    
    async def recall(self, memory_type: Optional[MemoryType] = None, limit: int = 10) -> List[Dict]:
        """Retrieve memories"""
        await self.connect()
        
        async with self.pool.acquire() as conn:
            if memory_type:
                rows = await conn.fetch("""
                    SELECT * FROM agent_memory 
                    WHERE agent_id = $1 AND memory_type = $2
                    ORDER BY relevance_score DESC, created_at DESC
                    LIMIT $3
                """, self.agent_id, memory_type.value, limit)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM agent_memory 
                    WHERE agent_id = $1
                    ORDER BY relevance_score DESC, created_at DESC
                    LIMIT $2
                """, self.agent_id, limit)
            
            return [dict(row) for row in rows]
    
    async def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search memories semantically"""
        await self.connect()
        
        # For now, simple text search. Later: vector similarity with embeddings
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM agent_memory 
                WHERE agent_id = $1 AND content::text ILIKE $2
                ORDER BY relevance_score DESC, created_at DESC
                LIMIT $3
            """, self.agent_id, f"%{query}%", limit)
            
            return [dict(row) for row in rows]
    
    async def forget(self, memory_id: str):
        """Delete a specific memory"""
        await self.connect()
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM agent_memory WHERE memory_id = $1 AND agent_id = $2
            """, memory_id, self.agent_id)

class AgentCommunication:
    """Inter-agent communication system"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.pool = None
    
    async def connect(self):
        """Connect to Supabase"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    
    async def send(self, to_agent: str, message_type: MessageType, content: Dict[str, Any], priority: int = 5):
        """Send message to another agent"""
        await self.connect()
        
        async with self.pool.acquire() as conn:
            message_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO agent_communications 
                (message_id, from_agent, to_agent, message_type, content, priority, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, message_id, self.agent_id, to_agent, message_type.value, json.dumps(content), priority, datetime.utcnow())
            
            return message_id
    
    async def receive(self, limit: int = 10) -> List[Dict]:
        """Receive messages for this agent"""
        await self.connect()
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM agent_communications 
                WHERE to_agent = $1 AND processed = FALSE
                ORDER BY priority DESC, created_at ASC
                LIMIT $2
            """, self.agent_id, limit)
            
            # Mark as processed
            for row in rows:
                await conn.execute("""
                    UPDATE agent_communications SET processed = TRUE WHERE message_id = $1
                """, row['message_id'])
            
            return [dict(row) for row in rows]
    
    async def broadcast(self, message_type: MessageType, content: Dict[str, Any], priority: int = 5):
        """Broadcast to all agents"""
        await self.connect()
        
        async with self.pool.acquire() as conn:
            # Get all active agents
            agents = await conn.fetch("SELECT agent_id FROM agent_registry WHERE status != 'offline'")
            
            # Send to each
            for agent in agents:
                if agent['agent_id'] != self.agent_id:
                    await self.send(agent['agent_id'], message_type, content, priority)

class Agent:
    """Base class for all AI agents"""
    
    def __init__(self, name: str, specialization: str, capabilities: List[str]):
        self.agent_id = str(uuid.uuid4())
        self.name = name
        self.specialization = specialization
        self.capabilities = capabilities
        self.status = AgentStatus.IDLE
        self.memory = AgentMemory(self.agent_id)
        self.communication = AgentCommunication(self.agent_id)
        self.pool = None
        
        # LLM configuration (to be set based on agent type)
        self.llm_model = "gpt-4"
        self.llm_temperature = 0.7
    
    async def initialize(self):
        """Initialize agent and register in database"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
        
        async with self.pool.acquire() as conn:
            # Register agent
            await conn.execute("""
                INSERT INTO agent_registry (agent_id, agent_type, agent_name, specialization, capabilities, last_active, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (agent_id) DO UPDATE SET
                    last_active = $6,
                    status = $7
            """, self.agent_id, 'orchestration', self.name, self.specialization, json.dumps(self.capabilities), 
                datetime.utcnow(), self.status.value)
        
        logger.info(f"Agent {self.name} initialized with ID {self.agent_id}")
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process information and make decisions"""
        self.status = AgentStatus.THINKING
        await self._update_status()
        
        try:
            # Recall relevant memories
            memories = await self.memory.recall(limit=5)
            
            # Search for related experiences
            if 'error' in context:
                error_memories = await self.memory.search(context['error'], limit=3)
                memories.extend(error_memories)
            
            # Process with LLM (placeholder - integrate with actual LLM)
            decision = await self._llm_process(context, memories)
            
            # Store this thinking process
            await self.memory.remember(
                MemoryType.EXPERIENCE,
                {
                    'context': context,
                    'decision': decision,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            self.status = AgentStatus.IDLE
            await self._update_status()
            
            return decision
            
        except Exception as e:
            logger.error(f"Agent {self.name} thinking error: {e}")
            self.status = AgentStatus.ERROR
            await self._update_status()
            
            # Remember the error
            await self.memory.remember(
                MemoryType.ERROR,
                {
                    'context': context,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            raise
    
    async def act(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action"""
        self.status = AgentStatus.ACTING
        await self._update_status()
        
        try:
            # Execute based on action type
            result = await self._execute_action(action)
            
            # Remember the action and result
            await self.memory.remember(
                MemoryType.EXPERIENCE,
                {
                    'action': action,
                    'result': result,
                    'success': result.get('success', False),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # If successful, remember as a solution
            if result.get('success'):
                await self.memory.remember(
                    MemoryType.SOLUTION,
                    {
                        'problem': action.get('problem'),
                        'solution': action,
                        'result': result,
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    relevance=0.9
                )
            
            self.status = AgentStatus.IDLE
            await self._update_status()
            
            return result
            
        except Exception as e:
            logger.error(f"Agent {self.name} action error: {e}")
            self.status = AgentStatus.ERROR
            await self._update_status()
            
            # Remember the failed action
            await self.memory.remember(
                MemoryType.ERROR,
                {
                    'action': action,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            raise
    
    async def communicate(self, other_agent: str, message: Dict[str, Any]) -> Optional[Dict]:
        """Communicate with another agent"""
        self.status = AgentStatus.COMMUNICATING
        await self._update_status()
        
        # Send message
        message_id = await self.communication.send(
            other_agent,
            MessageType.QUERY,
            message
        )
        
        # Wait for response (with timeout)
        await asyncio.sleep(1)  # Give other agent time to process
        
        # Check for responses
        messages = await self.communication.receive(limit=1)
        
        self.status = AgentStatus.IDLE
        await self._update_status()
        
        if messages:
            return messages[0]
        return None
    
    async def learn(self):
        """Learn from experiences and improve"""
        self.status = AgentStatus.LEARNING
        await self._update_status()
        
        try:
            # Get recent experiences
            experiences = await self.memory.recall(MemoryType.EXPERIENCE, limit=20)
            
            # Identify patterns
            patterns = await self._identify_patterns(experiences)
            
            # Store insights
            for pattern in patterns:
                await self.memory.remember(
                    MemoryType.PATTERN,
                    pattern,
                    relevance=pattern.get('confidence', 0.5)
                )
            
            # Get recent errors
            errors = await self.memory.recall(MemoryType.ERROR, limit=10)
            
            # Find solutions for common errors
            for error in errors:
                solution = await self._find_solution(error)
                if solution:
                    await self.memory.remember(
                        MemoryType.SOLUTION,
                        {
                            'error': error,
                            'solution': solution,
                            'timestamp': datetime.utcnow().isoformat()
                        },
                        relevance=0.8
                    )
            
            self.status = AgentStatus.IDLE
            await self._update_status()
            
            logger.info(f"Agent {self.name} completed learning cycle")
            
        except Exception as e:
            logger.error(f"Agent {self.name} learning error: {e}")
            self.status = AgentStatus.ERROR
            await self._update_status()
    
    async def _update_status(self):
        """Update agent status in database"""
        if not self.pool:
            return
            
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE agent_registry 
                SET status = $1, last_active = $2
                WHERE agent_id = $3
            """, self.status.value, datetime.utcnow(), self.agent_id)
    
    async def _llm_process(self, context: Dict, memories: List[Dict]) -> Dict:
        """Process with LLM (placeholder for actual implementation)"""
        # This will be replaced with actual LLM calls
        # For now, return a simple decision structure
        return {
            'action': 'investigate',
            'confidence': 0.8,
            'reasoning': 'Based on context and past experiences',
            'next_steps': ['analyze', 'test', 'deploy']
        }
    
    async def _execute_action(self, action: Dict) -> Dict:
        """Execute an action (to be overridden by specific agents)"""
        # Base implementation - specific agents will override
        return {
            'success': True,
            'result': 'Action executed',
            'details': action
        }
    
    async def _identify_patterns(self, experiences: List[Dict]) -> List[Dict]:
        """Identify patterns in experiences"""
        # Placeholder for pattern recognition
        # Will use ML/statistical analysis
        patterns = []
        
        # Simple example: count error types
        error_counts = {}
        for exp in experiences:
            if 'error' in exp.get('content', {}):
                error_type = exp['content'].get('error_type', 'unknown')
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        for error_type, count in error_counts.items():
            if count > 2:  # Pattern threshold
                patterns.append({
                    'type': 'recurring_error',
                    'error_type': error_type,
                    'frequency': count,
                    'confidence': min(count / 10, 1.0)
                })
        
        return patterns
    
    async def _find_solution(self, error: Dict) -> Optional[Dict]:
        """Find solution for an error"""
        # Search for similar solved errors
        error_text = str(error.get('content', {}).get('error', ''))
        similar_solutions = await self.memory.search(error_text, limit=3)
        
        for mem in similar_solutions:
            if mem['memory_type'] == MemoryType.SOLUTION.value:
                return mem['content']
        
        return None
    
    async def run(self):
        """Main agent loop"""
        await self.initialize()
        
        while True:
            try:
                # Check for messages
                messages = await self.communication.receive(limit=5)
                
                for message in messages:
                    # Process message
                    context = message['content']
                    
                    # Think about it
                    decision = await self.think(context)
                    
                    # Act on decision
                    if decision.get('action'):
                        result = await self.act(decision)
                        
                        # Report back if requested
                        if message['message_type'] == MessageType.QUERY.value:
                            await self.communication.send(
                                message['from_agent'],
                                MessageType.RESPONSE,
                                result
                            )
                
                # Periodic learning
                if asyncio.get_event_loop().time() % 3600 < 60:  # Every hour
                    await self.learn()
                
                # Sleep before next cycle
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Agent {self.name} main loop error: {e}")
                await asyncio.sleep(30)  # Wait longer on error

# Make base classes available
__all__ = [
    'Agent',
    'AgentMemory', 
    'AgentCommunication',
    'AgentStatus',
    'MemoryType',
    'MessageType',
    'SystemComponent'
]