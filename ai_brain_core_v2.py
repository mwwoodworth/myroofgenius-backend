"""
AI Brain Core v2 - Central Intelligence System
Clean version without hardcoded credentials
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio

logger = logging.getLogger(__name__)

# Use environment variables for any sensitive config
DATABASE_URL = os.getenv("DATABASE_URL")
AI_API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")


class AIBrainCore:
    """
    Central AI Brain that coordinates all AI operations.
    Manages agents, neural pathways, decisions, and memory.
    """

    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.neural_pathways: Dict[str, Dict[str, Any]] = {}
        self.memory: Dict[str, List] = {
            "short_term": [],
            "long_term": [],
            "patterns": []
        }
        self.decision_engine_running = False
        self.decisions_made = 0
        self.learning_rate = 0.1
        self.start_time = datetime.now()
        self.api_calls = 0
        self.success_rate = 100.0
        self._initialized = False

    async def initialize(self):
        """Initialize the AI Brain Core"""
        if self._initialized:
            return

        logger.info("Initializing AI Brain Core v2...")

        # Register default agents
        self.agents = {
            "orchestrator": {
                "name": "Master Orchestrator",
                "status": "active",
                "capabilities": ["coordination", "decision_routing", "task_delegation"]
            },
            "analyzer": {
                "name": "Data Analyzer",
                "status": "active",
                "capabilities": ["pattern_recognition", "anomaly_detection", "insights"]
            },
            "executor": {
                "name": "Task Executor",
                "status": "active",
                "capabilities": ["automation", "workflow_execution", "integration"]
            },
            "learner": {
                "name": "Learning Agent",
                "status": "active",
                "capabilities": ["model_training", "feedback_processing", "adaptation"]
            }
        }

        # Initialize neural pathways
        self.neural_pathways = {
            "decision_pathway": {"active": True, "strength": 0.8},
            "memory_pathway": {"active": True, "strength": 0.9},
            "learning_pathway": {"active": True, "strength": 0.7},
            "action_pathway": {"active": True, "strength": 0.85}
        }

        self.decision_engine_running = True
        self._initialized = True
        logger.info("AI Brain Core v2 initialized successfully")

    async def make_decision(
        self,
        context: Dict[str, Any],
        options: List[Any],
        urgency: str = "normal"
    ) -> Dict[str, Any]:
        """
        Make an intelligent decision based on context and options.
        """
        self.decisions_made += 1
        self.api_calls += 1

        # Simple decision logic (can be enhanced with actual AI calls)
        if not options:
            return {
                "chosen": None,
                "confidence": 0.0,
                "reasoning": "No options provided"
            }

        # Score each option based on context
        scored_options = []
        for i, option in enumerate(options):
            score = 0.5 + (0.1 * (len(options) - i))  # Simple scoring
            if urgency == "high":
                score += 0.1
            scored_options.append((option, min(score, 1.0)))

        # Choose the highest scored option
        best_option, confidence = max(scored_options, key=lambda x: x[1])

        decision = {
            "chosen": best_option,
            "confidence": confidence,
            "reasoning": f"Selected based on scoring algorithm. Context keys: {list(context.keys())}",
            "alternatives": [opt for opt, _ in scored_options if opt != best_option][:3]
        }

        # Store in short-term memory
        self.memory["short_term"].append({
            "type": "decision",
            "decision": decision,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })

        # Keep memory manageable
        if len(self.memory["short_term"]) > 100:
            self.memory["short_term"] = self.memory["short_term"][-100:]

        return decision

    async def learn_from_feedback(self, decision_id: str, outcome: str, feedback: Dict[str, Any]):
        """Process feedback to improve future decisions"""
        self.memory["patterns"].append({
            "decision_id": decision_id,
            "outcome": outcome,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })

        # Adjust learning rate based on feedback
        if outcome == "success":
            self.success_rate = min(100.0, self.success_rate + 0.1)
        else:
            self.success_rate = max(0.0, self.success_rate - 0.5)
            self.learning_rate = min(0.5, self.learning_rate + 0.01)

        return {"status": "learned", "new_learning_rate": self.learning_rate}

    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent"""
        return self.agents.get(agent_id)

    async def activate_agent(self, agent_id: str) -> Dict[str, Any]:
        """Activate a specific agent"""
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = "active"
            return {"status": "activated", "agent_id": agent_id}
        return {"status": "not_found", "agent_id": agent_id}

    async def deactivate_agent(self, agent_id: str) -> Dict[str, Any]:
        """Deactivate a specific agent"""
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = "inactive"
            return {"status": "deactivated", "agent_id": agent_id}
        return {"status": "not_found", "agent_id": agent_id}

    async def store_memory(self, memory_type: str, data: Dict[str, Any]):
        """Store data in memory"""
        if memory_type not in self.memory:
            self.memory[memory_type] = []
        self.memory[memory_type].append({
            **data,
            "stored_at": datetime.now().isoformat()
        })
        return {"status": "stored", "type": memory_type}

    async def recall_memory(self, memory_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recall memories of a specific type"""
        memories = self.memory.get(memory_type, [])
        return memories[-limit:] if memories else []

    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        return {
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_decisions": self.decisions_made,
            "success_rate": self.success_rate,
            "learning_rate": self.learning_rate,
            "api_calls": self.api_calls,
            "agents": {
                "total": len(self.agents),
                "active": sum(1 for a in self.agents.values() if a.get("status") == "active")
            },
            "memory": {
                "short_term_size": len(self.memory.get("short_term", [])),
                "long_term_size": len(self.memory.get("long_term", [])),
                "patterns_learned": len(self.memory.get("patterns", []))
            },
            "neural_pathways": {
                "total": len(self.neural_pathways),
                "active": sum(1 for p in self.neural_pathways.values() if p.get("active"))
            }
        }
