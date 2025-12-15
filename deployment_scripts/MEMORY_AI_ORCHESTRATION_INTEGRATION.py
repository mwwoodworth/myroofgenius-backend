#!/usr/bin/env python3
"""
MEMORY-AI ORCHESTRATION INTEGRATION
Connects persistent memory with all AI agents, LangGraphOS, and AUREA
to create a truly intelligent, learning system.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiohttp
import os
import sys

# Add backend path
sys.path.append('/home/mwwoodworth/code/fastapi-operator-env/apps/backend')

# Configuration
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "<ANTHROPIC_API_KEY_REDACTED>...")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "<OPENAI_API_KEY_REDACTED>...")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "<GOOGLE_API_KEY_REDACTED>")

logger = logging.getLogger("MemoryAIOrchestration")


class MemoryAwareAIOrchestrator:
    """Orchestrates all AI agents with persistent memory at the core"""
    
    def __init__(self):
        self.session = None
        self.memory_context = {}
        self.agent_registry = {}
        self.active_workflows = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self.initialize_orchestration()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def initialize_orchestration(self):
        """Initialize AI orchestration with memory integration"""
        logger.info("🤖 Initializing Memory-Aware AI Orchestration...")
        
        # Register all AI agents
        await self.register_ai_agents()
        
        # Load memory context
        await self.load_memory_context()
        
        # Start orchestration loops
        asyncio.create_task(self.memory_sync_loop())
        asyncio.create_task(self.agent_coordination_loop())
        asyncio.create_task(self.workflow_optimization_loop())
        
        logger.info("✅ AI Orchestration initialized with memory integration")
        
    async def register_ai_agents(self):
        """Register all available AI agents with their capabilities"""
        
        self.agent_registry = {
            "aurea_executive": {
                "type": "executive",
                "capabilities": ["decision_making", "natural_language", "system_control"],
                "memory_access": "full",
                "priority": 1,
                "endpoint": f"{BACKEND_URL}/api/v1/aurea/executive"
            },
            "claude_analyst": {
                "type": "analyst",
                "capabilities": ["code_analysis", "problem_solving", "documentation"],
                "memory_access": "read_write",
                "priority": 2,
                "endpoint": f"{BACKEND_URL}/api/v1/ai-services/claude"
            },
            "gpt_developer": {
                "type": "developer",
                "capabilities": ["code_generation", "refactoring", "optimization"],
                "memory_access": "read_write",
                "priority": 2,
                "endpoint": f"{BACKEND_URL}/api/v1/ai-services/openai"
            },
            "gemini_researcher": {
                "type": "researcher",
                "capabilities": ["market_research", "data_analysis", "insights"],
                "memory_access": "read_write",
                "priority": 3,
                "endpoint": f"{BACKEND_URL}/api/v1/ai-services/gemini"
            },
            "langgraph_planner": {
                "type": "planner",
                "capabilities": ["workflow_planning", "task_decomposition", "scheduling"],
                "memory_access": "read_write",
                "priority": 2,
                "endpoint": f"{BACKEND_URL}/api/v1/langgraphos/plan"
            },
            "langgraph_executor": {
                "type": "executor",
                "capabilities": ["task_execution", "monitoring", "error_handling"],
                "memory_access": "read_write",
                "priority": 2,
                "endpoint": f"{BACKEND_URL}/api/v1/langgraphos/execute"
            }
        }
        
        logger.info(f"Registered {len(self.agent_registry)} AI agents")
        
    async def load_memory_context(self):
        """Load relevant memory context for all agents"""
        
        # Get operational procedures
        async with self.session.get(
            f"{BACKEND_URL}/api/v1/memory/search",
            params={"memory_type": "operational_procedure", "limit": 50}
        ) as response:
            if response.status == 200:
                procedures = await response.json()
                self.memory_context['procedures'] = procedures.get('results', [])
                
        # Get recent decisions
        async with self.session.get(
            f"{BACKEND_URL}/api/v1/memory/search",
            params={"memory_type": "decision_record", "limit": 20}
        ) as response:
            if response.status == 200:
                decisions = await response.json()
                self.memory_context['recent_decisions'] = decisions.get('results', [])
                
        # Get learning insights
        async with self.session.get(
            f"{BACKEND_URL}/api/v1/memory/search",
            params={"memory_type": "learning_insight", "limit": 30}
        ) as response:
            if response.status == 200:
                insights = await response.json()
                self.memory_context['insights'] = insights.get('results', [])
                
        logger.info(f"Loaded memory context: {len(self.memory_context)} categories")
        
    async def execute_with_memory(self, 
                                 task: str,
                                 agent_type: str = None,
                                 context: Dict = None) -> Dict:
        """Execute a task using appropriate AI agent with full memory context"""
        
        # Get relevant memory for task
        task_memory = await self.get_task_memory(task)
        
        # Select best agent if not specified
        if not agent_type:
            agent_type = await self.select_best_agent(task, task_memory)
            
        agent = self.agent_registry.get(agent_type)
        if not agent:
            logger.error(f"Agent not found: {agent_type}")
            return {"error": "Agent not found"}
            
        # Prepare enhanced context with memory
        enhanced_context = {
            "task": task,
            "memory_context": task_memory,
            "global_insights": self.memory_context.get('insights', []),
            "user_context": context or {},
            "agent_capabilities": agent['capabilities'],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log task initiation
        await self.log_to_memory(
            title=f"Task Initiated: {task}",
            content={
                "task": task,
                "selected_agent": agent_type,
                "context_size": len(str(enhanced_context))
            },
            memory_type="user_interaction"
        )
        
        # Execute with selected agent
        try:
            result = await self.execute_agent_task(agent, enhanced_context)
            
            # Log successful execution
            await self.log_to_memory(
                title=f"Task Completed: {task}",
                content={
                    "task": task,
                    "agent": agent_type,
                    "success": True,
                    "result_summary": str(result)[:500]
                },
                memory_type="deployment_log"
            )
            
            # Learn from execution
            await self.learn_from_execution(task, agent_type, result, True)
            
            return result
            
        except Exception as e:
            # Log error
            await self.log_to_memory(
                title=f"Task Failed: {task}",
                content={
                    "task": task,
                    "agent": agent_type,
                    "error": str(e),
                    "context": enhanced_context
                },
                memory_type="error_pattern"
            )
            
            # Learn from failure
            await self.learn_from_execution(task, agent_type, str(e), False)
            
            # Try fallback agent
            fallback_result = await self.try_fallback_agent(task, agent_type, enhanced_context)
            return fallback_result
            
    async def create_intelligent_workflow(self, 
                                        goal: str,
                                        constraints: Dict = None) -> Dict:
        """Create an intelligent workflow using memory and multiple agents"""
        
        workflow_id = f"workflow_{datetime.utcnow().timestamp()}"
        
        # Get relevant procedures from memory
        procedures = await self.get_relevant_procedures(goal)
        
        # Plan workflow using LangGraph
        plan = await self.execute_with_memory(
            task=f"Create workflow plan for: {goal}",
            agent_type="langgraph_planner",
            context={"constraints": constraints, "procedures": procedures}
        )
        
        workflow = {
            "id": workflow_id,
            "goal": goal,
            "plan": plan,
            "status": "planned",
            "created_at": datetime.utcnow().isoformat(),
            "agents_involved": [],
            "memory_references": [p['id'] for p in procedures if 'id' in p]
        }
        
        # Store workflow in memory
        await self.log_to_memory(
            title=f"Workflow Created: {goal}",
            content=workflow,
            memory_type="operational_procedure",
            importance=0.8
        )
        
        # Register active workflow
        self.active_workflows[workflow_id] = workflow
        
        # Start execution
        asyncio.create_task(self.execute_workflow(workflow_id))
        
        return workflow
        
    async def execute_workflow(self, workflow_id: str):
        """Execute a workflow with continuous memory updates"""
        
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return
            
        workflow['status'] = 'executing'
        workflow['started_at'] = datetime.utcnow().isoformat()
        
        try:
            # Execute each step in the plan
            for step in workflow['plan'].get('steps', []):
                # Get memory context for step
                step_memory = await self.get_task_memory(step['description'])
                
                # Execute step with appropriate agent
                result = await self.execute_with_memory(
                    task=step['description'],
                    agent_type=step.get('agent'),
                    context={
                        "workflow_id": workflow_id,
                        "step_number": step['number'],
                        "previous_results": workflow.get('results', [])
                    }
                )
                
                # Store step result
                if 'results' not in workflow:
                    workflow['results'] = []
                workflow['results'].append({
                    "step": step['number'],
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Check if should continue
                if not result.get('success', True):
                    workflow['status'] = 'failed'
                    break
                    
            if workflow['status'] != 'failed':
                workflow['status'] = 'completed'
                
        except Exception as e:
            workflow['status'] = 'error'
            workflow['error'] = str(e)
            
        workflow['completed_at'] = datetime.utcnow().isoformat()
        
        # Store final workflow state
        await self.log_to_memory(
            title=f"Workflow Completed: {workflow['goal']}",
            content=workflow,
            memory_type="deployment_log",
            importance=0.9
        )
        
        # Learn from workflow execution
        await self.analyze_workflow_performance(workflow)
        
    async def memory_sync_loop(self):
        """Continuously sync memory across all agents"""
        
        while True:
            try:
                # Update memory context
                await self.load_memory_context()
                
                # Broadcast updates to active agents
                for agent_name, agent in self.agent_registry.items():
                    if agent['memory_access'] in ['full', 'read_write']:
                        # Notify agent of memory updates
                        await self.notify_agent_memory_update(agent_name)
                        
                await asyncio.sleep(60)  # 1 minute
                
            except Exception as e:
                logger.error(f"Memory sync error: {str(e)}")
                await asyncio.sleep(30)
                
    async def agent_coordination_loop(self):
        """Coordinate agents for collaborative tasks"""
        
        while True:
            try:
                # Check for multi-agent tasks
                multi_agent_tasks = await self.get_multi_agent_tasks()
                
                for task in multi_agent_tasks:
                    # Coordinate agents
                    await self.coordinate_agents_for_task(task)
                    
                await asyncio.sleep(30)  # 30 seconds
                
            except Exception as e:
                logger.error(f"Agent coordination error: {str(e)}")
                await asyncio.sleep(30)
                
    async def workflow_optimization_loop(self):
        """Continuously optimize workflows based on performance"""
        
        while True:
            try:
                # Analyze completed workflows
                completed = [w for w in self.active_workflows.values() 
                           if w['status'] in ['completed', 'failed']]
                           
                for workflow in completed:
                    # Generate optimization suggestions
                    optimizations = await self.generate_workflow_optimizations(workflow)
                    
                    # Store optimizations
                    for opt in optimizations:
                        await self.log_to_memory(
                            title=f"Workflow Optimization: {opt['title']}",
                            content=opt,
                            memory_type="system_improvement",
                            importance=0.7
                        )
                        
                # Clean up old workflows
                self.clean_old_workflows()
                
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Workflow optimization error: {str(e)}")
                await asyncio.sleep(60)
                
    # Helper methods
    async def get_task_memory(self, task: str) -> Dict:
        """Get relevant memory for a specific task"""
        
        memory = {}
        
        # Search for similar tasks
        async with self.session.post(
            f"{BACKEND_URL}/api/v1/memory/search",
            json={"query": task, "limit": 10}
        ) as response:
            if response.status == 200:
                results = await response.json()
                memory['similar_tasks'] = results.get('results', [])
                
        # Get relevant procedures
        for proc in self.memory_context.get('procedures', []):
            if any(trigger in task.lower() for trigger in proc.get('tags', [])):
                if 'relevant_procedures' not in memory:
                    memory['relevant_procedures'] = []
                memory['relevant_procedures'].append(proc)
                
        return memory
        
    async def select_best_agent(self, task: str, task_memory: Dict) -> str:
        """Select the best agent for a task based on capabilities and history"""
        
        # Analyze task requirements
        task_lower = task.lower()
        
        # Score agents based on task match
        scores = {}
        for agent_name, agent in self.agent_registry.items():
            score = 0
            
            # Check capability match
            for capability in agent['capabilities']:
                if capability.replace('_', ' ') in task_lower:
                    score += 10
                    
            # Check historical performance
            for similar_task in task_memory.get('similar_tasks', []):
                if similar_task.get('meta_data', {}).get('agent') == agent_name:
                    if similar_task.get('meta_data', {}).get('success', False):
                        score += 5
                    else:
                        score -= 2
                        
            scores[agent_name] = score
            
        # Select highest scoring agent
        best_agent = max(scores, key=scores.get)
        logger.info(f"Selected agent {best_agent} for task: {task}")
        
        return best_agent
        
    async def execute_agent_task(self, agent: Dict, context: Dict) -> Dict:
        """Execute a task with a specific agent"""
        
        # Make API call to agent endpoint
        async with self.session.post(
            agent['endpoint'],
            json={"context": context},
            headers={"Authorization": f"Bearer {self.get_agent_api_key(agent['type'])}"}
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Agent execution failed: {await response.text()}")
                
    async def log_to_memory(self, title: str, content: Any, 
                          memory_type: str, importance: float = 0.5):
        """Log information to persistent memory"""
        
        async with self.session.post(
            f"{BACKEND_URL}/api/v1/memory/create",
            json={
                "title": title,
                "content": content,
                "memory_type": memory_type,
                "importance_score": importance,
                "tags": ["ai_orchestration", memory_type]
            }
        ) as response:
            if response.status != 200:
                logger.error(f"Failed to log to memory: {await response.text()}")
                
    async def learn_from_execution(self, task: str, agent: str, 
                                 result: Any, success: bool):
        """Learn from task execution to improve future performance"""
        
        learning = {
            "task": task,
            "agent": agent,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if success:
            learning['pattern'] = "success"
            learning['insights'] = [
                f"Agent {agent} successfully handled task type: {task[:50]}",
                "Consider using similar approach for related tasks"
            ]
        else:
            learning['pattern'] = "failure"
            learning['insights'] = [
                f"Agent {agent} failed on task type: {task[:50]}",
                "Consider using different agent or approach",
                f"Error details: {str(result)[:200]}"
            ]
            
        await self.log_to_memory(
            title=f"Execution Learning: {task[:50]}",
            content=learning,
            memory_type="learning_insight",
            importance=0.7 if success else 0.9
        )
        
    async def get_relevant_procedures(self, goal: str) -> List[Dict]:
        """Get procedures relevant to a goal"""
        
        relevant = []
        goal_lower = goal.lower()
        
        for proc in self.memory_context.get('procedures', []):
            # Check if procedure matches goal
            proc_content = proc.get('content', {})
            if isinstance(proc_content, str):
                try:
                    proc_content = json.loads(proc_content)
                except:
                    continue
                    
            if any(word in goal_lower for word in proc_content.get('triggers', [])):
                relevant.append(proc)
                
        return relevant
        
    def get_agent_api_key(self, agent_type: str) -> str:
        """Get API key for agent type"""
        
        if agent_type in ['executive', 'analyst']:
            return ANTHROPIC_API_KEY
        elif agent_type == 'developer':
            return OPENAI_API_KEY
        elif agent_type == 'researcher':
            return GEMINI_API_KEY
        else:
            return ""
            
    async def try_fallback_agent(self, task: str, failed_agent: str, 
                                context: Dict) -> Dict:
        """Try a fallback agent when primary fails"""
        
        # Get agents with similar capabilities
        failed_capabilities = self.agent_registry[failed_agent]['capabilities']
        
        for agent_name, agent in self.agent_registry.items():
            if agent_name != failed_agent:
                # Check capability overlap
                overlap = set(agent['capabilities']) & set(failed_capabilities)
                if overlap:
                    logger.info(f"Trying fallback agent: {agent_name}")
                    try:
                        return await self.execute_agent_task(agent, context)
                    except:
                        continue
                        
        return {"error": "All agents failed", "original_task": task}
        
    async def notify_agent_memory_update(self, agent_name: str):
        """Notify an agent of memory updates"""
        # This would send memory updates to agents that maintain state
        pass
        
    async def get_multi_agent_tasks(self) -> List[Dict]:
        """Get tasks that require multiple agents"""
        # This would identify complex tasks needing coordination
        return []
        
    async def coordinate_agents_for_task(self, task: Dict):
        """Coordinate multiple agents for a complex task"""
        # This would orchestrate multi-agent collaboration
        pass
        
    async def generate_workflow_optimizations(self, workflow: Dict) -> List[Dict]:
        """Generate optimization suggestions for workflows"""
        
        optimizations = []
        
        # Analyze execution time
        if 'started_at' in workflow and 'completed_at' in workflow:
            duration = (datetime.fromisoformat(workflow['completed_at']) - 
                      datetime.fromisoformat(workflow['started_at'])).total_seconds()
                      
            if duration > 300:  # More than 5 minutes
                optimizations.append({
                    "title": "Workflow Duration Optimization",
                    "suggestion": "Consider parallelizing independent steps",
                    "potential_improvement": "50% time reduction"
                })
                
        # Analyze failures
        if workflow['status'] == 'failed':
            optimizations.append({
                "title": "Failure Prevention",
                "suggestion": "Add validation steps before critical operations",
                "failure_point": workflow.get('results', [])[-1] if workflow.get('results') else None
            })
            
        return optimizations
        
    async def analyze_workflow_performance(self, workflow: Dict):
        """Analyze workflow performance for improvements"""
        
        performance = {
            "workflow_id": workflow['id'],
            "goal": workflow['goal'],
            "status": workflow['status'],
            "duration": None,
            "steps_completed": len(workflow.get('results', [])),
            "agents_used": list(set(workflow.get('agents_involved', []))),
            "memory_efficiency": len(workflow.get('memory_references', []))
        }
        
        if 'started_at' in workflow and 'completed_at' in workflow:
            performance['duration'] = (
                datetime.fromisoformat(workflow['completed_at']) - 
                datetime.fromisoformat(workflow['started_at'])
            ).total_seconds()
            
        await self.log_to_memory(
            title=f"Workflow Performance Analysis: {workflow['goal'][:50]}",
            content=performance,
            memory_type="performance_metric",
            importance=0.6
        )
        
    def clean_old_workflows(self):
        """Remove old completed workflows from memory"""
        
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        to_remove = []
        for wf_id, workflow in self.active_workflows.items():
            if workflow['status'] in ['completed', 'failed', 'error']:
                if 'completed_at' in workflow:
                    completed_at = datetime.fromisoformat(workflow['completed_at'])
                    if completed_at < cutoff:
                        to_remove.append(wf_id)
                        
        for wf_id in to_remove:
            del self.active_workflows[wf_id]
            
        if to_remove:
            logger.info(f"Cleaned {len(to_remove)} old workflows")


async def main():
    """Main entry point for testing"""
    
    async with MemoryAwareAIOrchestrator() as orchestrator:
        # Example: Execute a task with memory context
        result = await orchestrator.execute_with_memory(
            task="Deploy the latest backend changes to production",
            context={"version": "3.1.195", "changes": "memory integration"}
        )
        print("Task result:", json.dumps(result, indent=2))
        
        # Example: Create an intelligent workflow
        workflow = await orchestrator.create_intelligent_workflow(
            goal="Implement and deploy a new feature for user authentication",
            constraints={"timeline": "2 hours", "testing_required": True}
        )
        print("Workflow created:", json.dumps(workflow, indent=2))
        
        # Keep running for background tasks
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())