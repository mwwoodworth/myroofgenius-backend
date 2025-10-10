#!/usr/bin/env python3
"""
PERSISTENT MEMORY OPERATIONAL FRAMEWORK
A comprehensive system that ensures persistent memory is the brain of BrainOps,
capturing all knowledge, establishing procedures, and continuously improving.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import hashlib
import aiohttp
from enum import Enum
import os
import sys

# Add backend path for imports
sys.path.append('/home/mwwoodworth/code/fastapi-operator-env/apps/backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
DATABASE_URL = "postgresql://postgres:Brain0ps2O2S@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres"
SUPABASE_URL = "https://yomagoqdmxszqtdwuhab.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTgzMzI3NiwiZXhwIjoyMDY1NDA5Mjc2fQ.7C3guJ_0moYGkdyeFmJ9cd2BmduB5NnU00erIIxH3gQ"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PersistentMemory")


class MemoryType(Enum):
    """Types of memory for categorization"""
    OPERATIONAL_PROCEDURE = "operational_procedure"
    SYSTEM_IMPROVEMENT = "system_improvement"
    ERROR_PATTERN = "error_pattern"
    SUCCESS_PATTERN = "success_pattern"
    DEPLOYMENT_LOG = "deployment_log"
    DECISION_RECORD = "decision_record"
    LEARNING_INSIGHT = "learning_insight"
    AUTOMATION_RULE = "automation_rule"
    PERFORMANCE_METRIC = "performance_metric"
    USER_INTERACTION = "user_interaction"


class PersistentMemoryFramework:
    """Core framework for persistent memory operations"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session = None
        self.memory_cache = {}
        self.operational_procedures = {}
        self.learning_patterns = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self.initialize_framework()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def initialize_framework(self):
        """Initialize the persistent memory framework"""
        logger.info("🧠 Initializing Persistent Memory Framework...")
        
        # Load existing operational procedures
        await self.load_operational_procedures()
        
        # Load learning patterns
        await self.load_learning_patterns()
        
        # Start background processes
        asyncio.create_task(self.continuous_learning_loop())
        asyncio.create_task(self.pattern_analysis_loop())
        asyncio.create_task(self.procedure_enforcement_loop())
        
        logger.info("✅ Persistent Memory Framework initialized")
        
    async def capture_knowledge(self, 
                              title: str,
                              content: Any,
                              memory_type: MemoryType,
                              tags: List[str] = None,
                              importance: float = 0.5,
                              metadata: Dict = None) -> Dict:
        """Capture any knowledge or event into persistent memory"""
        
        memory_entry = {
            "title": title,
            "content": content if isinstance(content, str) else json.dumps(content),
            "memory_type": memory_type.value,
            "tags": tags or [],
            "importance_score": importance,
            "meta_data": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in database
        async with self.session.post(
            f"{BACKEND_URL}/api/v1/memory/create",
            json=memory_entry
        ) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ Knowledge captured: {title}")
                
                # Update local cache
                self.memory_cache[result.get('id')] = memory_entry
                
                # Trigger learning if high importance
                if importance > 0.8:
                    await self.trigger_immediate_learning(memory_entry)
                    
                return result
            else:
                logger.error(f"Failed to capture knowledge: {await response.text()}")
                return None
                
    async def retrieve_knowledge(self, 
                               query: str = None,
                               memory_type: MemoryType = None,
                               tags: List[str] = None,
                               limit: int = 10) -> List[Dict]:
        """Retrieve relevant knowledge from memory"""
        
        params = {
            "limit": limit
        }
        
        if query:
            params["query"] = query
        if memory_type:
            params["memory_type"] = memory_type.value
        if tags:
            params["tags"] = ",".join(tags)
            
        async with self.session.get(
            f"{BACKEND_URL}/api/v1/memory/search",
            params=params
        ) as response:
            if response.status == 200:
                memories = await response.json()
                return memories.get('results', [])
            else:
                logger.error(f"Failed to retrieve knowledge: {await response.text()}")
                return []
                
    async def establish_procedure(self, 
                                name: str,
                                steps: List[Dict],
                                triggers: List[str],
                                expected_outcomes: Dict) -> Dict:
        """Establish a new operational procedure"""
        
        procedure = {
            "name": name,
            "steps": steps,
            "triggers": triggers,
            "expected_outcomes": expected_outcomes,
            "created_at": datetime.utcnow().isoformat(),
            "execution_count": 0,
            "success_rate": 0.0
        }
        
        # Store as operational procedure
        await self.capture_knowledge(
            title=f"Operational Procedure: {name}",
            content=procedure,
            memory_type=MemoryType.OPERATIONAL_PROCEDURE,
            tags=["procedure", "automation"] + triggers,
            importance=0.9,
            metadata={"procedure_id": hashlib.md5(name.encode()).hexdigest()}
        )
        
        # Cache locally for fast access
        self.operational_procedures[name] = procedure
        
        logger.info(f"📋 Established procedure: {name}")
        return procedure
        
    async def execute_procedure(self, procedure_name: str, context: Dict = None) -> Dict:
        """Execute an established procedure with strict adherence"""
        
        if procedure_name not in self.operational_procedures:
            logger.error(f"Procedure not found: {procedure_name}")
            return {"success": False, "error": "Procedure not found"}
            
        procedure = self.operational_procedures[procedure_name]
        execution_log = {
            "procedure": procedure_name,
            "started_at": datetime.utcnow().isoformat(),
            "context": context or {},
            "steps_completed": [],
            "errors": []
        }
        
        try:
            for step in procedure['steps']:
                logger.info(f"Executing step: {step['name']}")
                
                # Execute step based on type
                if step['type'] == 'command':
                    result = await self.execute_command(step['command'], context)
                elif step['type'] == 'check':
                    result = await self.execute_check(step['condition'], context)
                elif step['type'] == 'ai_action':
                    result = await self.execute_ai_action(step['action'], context)
                else:
                    result = {"success": False, "error": f"Unknown step type: {step['type']}"}
                    
                execution_log['steps_completed'].append({
                    "step": step['name'],
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                if not result.get('success', False):
                    execution_log['errors'].append(result.get('error', 'Unknown error'))
                    if step.get('critical', True):
                        break
                        
            execution_log['completed_at'] = datetime.utcnow().isoformat()
            execution_log['success'] = len(execution_log['errors']) == 0
            
            # Update procedure statistics
            procedure['execution_count'] += 1
            if execution_log['success']:
                procedure['success_rate'] = (
                    (procedure['success_rate'] * (procedure['execution_count'] - 1) + 1) /
                    procedure['execution_count']
                )
            else:
                procedure['success_rate'] = (
                    (procedure['success_rate'] * (procedure['execution_count'] - 1)) /
                    procedure['execution_count']
                )
                
            # Store execution log
            await self.capture_knowledge(
                title=f"Procedure Execution: {procedure_name}",
                content=execution_log,
                memory_type=MemoryType.DEPLOYMENT_LOG,
                tags=["execution", procedure_name],
                importance=0.6
            )
            
            # Learn from execution
            await self.learn_from_execution(procedure_name, execution_log)
            
            return execution_log
            
        except Exception as e:
            logger.error(f"Procedure execution failed: {str(e)}")
            execution_log['errors'].append(str(e))
            execution_log['success'] = False
            return execution_log
            
    async def learn_from_execution(self, procedure_name: str, execution_log: Dict):
        """Learn from procedure execution to improve future runs"""
        
        if execution_log['success']:
            # Capture success pattern
            await self.capture_knowledge(
                title=f"Success Pattern: {procedure_name}",
                content={
                    "procedure": procedure_name,
                    "duration": self.calculate_duration(
                        execution_log['started_at'],
                        execution_log['completed_at']
                    ),
                    "context_keys": list(execution_log['context'].keys()),
                    "steps_count": len(execution_log['steps_completed'])
                },
                memory_type=MemoryType.SUCCESS_PATTERN,
                tags=["success", procedure_name],
                importance=0.7
            )
        else:
            # Capture error pattern for improvement
            await self.capture_knowledge(
                title=f"Error Pattern: {procedure_name}",
                content={
                    "procedure": procedure_name,
                    "errors": execution_log['errors'],
                    "failed_at_step": len(execution_log['steps_completed']),
                    "context": execution_log['context']
                },
                memory_type=MemoryType.ERROR_PATTERN,
                tags=["error", procedure_name],
                importance=0.9
            )
            
    async def continuous_learning_loop(self):
        """Continuously analyze patterns and improve systems"""
        
        while True:
            try:
                logger.info("🔄 Running continuous learning cycle...")
                
                # Analyze recent errors
                error_patterns = await self.retrieve_knowledge(
                    memory_type=MemoryType.ERROR_PATTERN,
                    limit=50
                )
                
                if error_patterns:
                    improvements = await self.generate_improvements(error_patterns)
                    for improvement in improvements:
                        await self.implement_improvement(improvement)
                        
                # Analyze success patterns
                success_patterns = await self.retrieve_knowledge(
                    memory_type=MemoryType.SUCCESS_PATTERN,
                    limit=50
                )
                
                if success_patterns:
                    optimizations = await self.generate_optimizations(success_patterns)
                    for optimization in optimizations:
                        await self.implement_optimization(optimization)
                        
                # Wait before next cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Learning loop error: {str(e)}")
                await asyncio.sleep(60)
                
    async def pattern_analysis_loop(self):
        """Analyze patterns in memory to identify trends and insights"""
        
        while True:
            try:
                logger.info("📊 Analyzing patterns in memory...")
                
                # Get all recent memories
                recent_memories = await self.retrieve_knowledge(limit=100)
                
                # Group by type and analyze
                patterns = {}
                for memory in recent_memories:
                    mem_type = memory.get('memory_type', 'unknown')
                    if mem_type not in patterns:
                        patterns[mem_type] = []
                    patterns[mem_type].append(memory)
                    
                # Generate insights
                insights = []
                for mem_type, memories in patterns.items():
                    if len(memories) > 5:
                        insight = await self.analyze_memory_group(mem_type, memories)
                        if insight:
                            insights.append(insight)
                            
                # Store insights
                for insight in insights:
                    await self.capture_knowledge(
                        title=f"Pattern Insight: {insight['title']}",
                        content=insight,
                        memory_type=MemoryType.LEARNING_INSIGHT,
                        tags=["insight", "pattern"],
                        importance=0.8
                    )
                    
                await asyncio.sleep(600)  # 10 minutes
                
            except Exception as e:
                logger.error(f"Pattern analysis error: {str(e)}")
                await asyncio.sleep(60)
                
    async def procedure_enforcement_loop(self):
        """Ensure strict adherence to established procedures"""
        
        while True:
            try:
                logger.info("👮 Enforcing operational procedures...")
                
                # Check for procedure violations
                recent_actions = await self.retrieve_knowledge(
                    memory_type=MemoryType.DEPLOYMENT_LOG,
                    limit=20
                )
                
                for action in recent_actions:
                    if not action.get('followed_procedure', True):
                        await self.handle_procedure_violation(action)
                        
                # Update procedure effectiveness
                for name, procedure in self.operational_procedures.items():
                    if procedure['execution_count'] > 10 and procedure['success_rate'] < 0.8:
                        await self.revise_procedure(name, procedure)
                        
                await asyncio.sleep(180)  # 3 minutes
                
            except Exception as e:
                logger.error(f"Procedure enforcement error: {str(e)}")
                await asyncio.sleep(60)
                
    async def integrate_with_ai_orchestration(self):
        """Integrate memory with all AI agents and orchestration systems"""
        
        integration_config = {
            "aurea_executive": {
                "memory_types": [MemoryType.DECISION_RECORD, MemoryType.OPERATIONAL_PROCEDURE],
                "query_before_action": True,
                "store_all_decisions": True
            },
            "langgraph_agents": {
                "memory_types": [MemoryType.DEPLOYMENT_LOG, MemoryType.ERROR_PATTERN],
                "share_context": True,
                "collective_learning": True
            },
            "claude_subagents": {
                "memory_access": "full",
                "mandatory_logging": True,
                "pattern_sharing": True
            }
        }
        
        # Store integration configuration
        await self.capture_knowledge(
            title="AI Orchestration Memory Integration",
            content=integration_config,
            memory_type=MemoryType.OPERATIONAL_PROCEDURE,
            tags=["integration", "ai", "orchestration"],
            importance=1.0
        )
        
        return integration_config
        
    async def get_contextual_guidance(self, task: str, context: Dict = None) -> Dict:
        """Get guidance from memory for a specific task"""
        
        # Search for relevant procedures
        procedures = await self.retrieve_knowledge(
            query=task,
            memory_type=MemoryType.OPERATIONAL_PROCEDURE,
            limit=5
        )
        
        # Search for similar past executions
        past_executions = await self.retrieve_knowledge(
            query=task,
            memory_type=MemoryType.DEPLOYMENT_LOG,
            limit=10
        )
        
        # Search for relevant patterns
        patterns = await self.retrieve_knowledge(
            query=task,
            memory_type=MemoryType.SUCCESS_PATTERN,
            limit=5
        )
        
        guidance = {
            "task": task,
            "recommended_procedures": procedures,
            "similar_executions": past_executions,
            "success_patterns": patterns,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Generate specific recommendations
        if procedures:
            guidance["primary_recommendation"] = procedures[0]
            guidance["confidence"] = self.calculate_confidence(procedures, past_executions)
        else:
            guidance["primary_recommendation"] = None
            guidance["confidence"] = 0.0
            guidance["suggestion"] = "No established procedure found. Consider creating one after successful execution."
            
        return guidance
        
    # Helper methods
    async def execute_command(self, command: str, context: Dict) -> Dict:
        """Execute a system command"""
        # Implementation would execute actual commands
        return {"success": True, "output": f"Executed: {command}"}
        
    async def execute_check(self, condition: str, context: Dict) -> Dict:
        """Execute a condition check"""
        # Implementation would evaluate conditions
        return {"success": True, "result": True}
        
    async def execute_ai_action(self, action: str, context: Dict) -> Dict:
        """Execute an AI action through appropriate agent"""
        # Implementation would route to appropriate AI agent
        return {"success": True, "result": f"AI executed: {action}"}
        
    def calculate_duration(self, start: str, end: str) -> float:
        """Calculate duration between timestamps"""
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
        return (end_dt - start_dt).total_seconds()
        
    def calculate_confidence(self, procedures: List[Dict], executions: List[Dict]) -> float:
        """Calculate confidence score for recommendations"""
        if not procedures:
            return 0.0
            
        # Base confidence on procedure availability
        confidence = 0.5
        
        # Boost based on successful executions
        successful = [e for e in executions if e.get('content', {}).get('success', False)]
        if successful:
            confidence += 0.3 * (len(successful) / len(executions))
            
        # Boost based on procedure success rate
        if procedures[0].get('content', {}).get('success_rate', 0) > 0.8:
            confidence += 0.2
            
        return min(confidence, 1.0)
        
    async def generate_improvements(self, error_patterns: List[Dict]) -> List[Dict]:
        """Generate improvements from error patterns"""
        # This would use AI to analyze errors and suggest improvements
        return []
        
    async def generate_optimizations(self, success_patterns: List[Dict]) -> List[Dict]:
        """Generate optimizations from success patterns"""
        # This would use AI to identify optimization opportunities
        return []
        
    async def implement_improvement(self, improvement: Dict):
        """Implement a suggested improvement"""
        # This would apply the improvement to procedures or code
        pass
        
    async def implement_optimization(self, optimization: Dict):
        """Implement a suggested optimization"""
        # This would apply the optimization
        pass
        
    async def analyze_memory_group(self, mem_type: str, memories: List[Dict]) -> Optional[Dict]:
        """Analyze a group of memories for insights"""
        # This would use AI to find patterns in memory groups
        return None
        
    async def handle_procedure_violation(self, action: Dict):
        """Handle a procedure violation"""
        # This would enforce procedures and notify of violations
        pass
        
    async def revise_procedure(self, name: str, procedure: Dict):
        """Revise an underperforming procedure"""
        # This would use AI to improve procedures
        pass
        
    async def load_operational_procedures(self):
        """Load existing procedures from memory"""
        procedures = await self.retrieve_knowledge(
            memory_type=MemoryType.OPERATIONAL_PROCEDURE,
            limit=100
        )
        
        for proc in procedures:
            content = proc.get('content', {})
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except:
                    continue
                    
            if 'name' in content:
                self.operational_procedures[content['name']] = content
                
        logger.info(f"Loaded {len(self.operational_procedures)} operational procedures")
        
    async def load_learning_patterns(self):
        """Load existing learning patterns"""
        patterns = await self.retrieve_knowledge(
            memory_type=MemoryType.LEARNING_INSIGHT,
            limit=50
        )
        
        self.learning_patterns = patterns
        logger.info(f"Loaded {len(self.learning_patterns)} learning patterns")


async def main():
    """Main entry point for testing the framework"""
    
    async with PersistentMemoryFramework() as pmf:
        # Example: Establish a deployment procedure
        await pmf.establish_procedure(
            name="Backend Deployment",
            steps=[
                {"name": "Build Docker Image", "type": "command", "command": "docker build -t mwwoodworth/brainops-backend:latest ."},
                {"name": "Push to Registry", "type": "command", "command": "docker push mwwoodworth/brainops-backend:latest"},
                {"name": "Trigger Deployment", "type": "command", "command": "curl -X POST https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"},
                {"name": "Verify Health", "type": "check", "condition": "backend_health_ok"}
            ],
            triggers=["backend_code_change", "manual_deploy"],
            expected_outcomes={"deployment_time": "<300s", "health_check": "passing"}
        )
        
        # Example: Get guidance for a task
        guidance = await pmf.get_contextual_guidance(
            "Deploy backend with new changes",
            context={"version": "3.1.195", "changes": "memory improvements"}
        )
        
        print(json.dumps(guidance, indent=2))
        
        # Keep running for background tasks
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())