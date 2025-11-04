"""
AI Agent Service Layer - Orchestration of AI Agents
Handles delegation of tasks to AI agents on ports 6001-6006
"""
import asyncio
import httpx
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)

class AgentStatus(str, Enum):
    """Agent status enumeration"""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class AgentCapability(BaseModel):
    """Agent capability definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

class AIAgent(BaseModel):
    """AI Agent configuration"""
    name: str
    port: int
    url: str
    specialization: str
    capabilities: List[AgentCapability]
    status: AgentStatus = AgentStatus.UNKNOWN
    current_tasks: int = 0
    max_concurrent_tasks: int = 5
    last_check: Optional[datetime] = None
    performance_metrics: Dict[str, float] = {}

class TaskRequest(BaseModel):
    """Task request for AI agents"""
    agent_name: Optional[str] = None  # If None, will auto-select best agent
    task_type: str
    priority: TaskPriority = TaskPriority.NORMAL
    context: Dict[str, Any] = {}
    timeout: int = 300  # 5 minutes default
    callback_url: Optional[str] = None

class TaskResponse(BaseModel):
    """Task execution response"""
    task_id: str
    agent_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class WorkflowStep(BaseModel):
    """Single step in a workflow"""
    step_id: str
    agent_name: str
    task_type: str
    context: Dict[str, Any] = {}
    depends_on: List[str] = []  # Step IDs this step depends on
    timeout: int = 300

class WorkflowRequest(BaseModel):
    """Multi-step workflow request"""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    auto_retry: bool = True
    max_retries: int = 3

class AIAgentService:
    """Service for orchestrating AI agents"""
    
    def __init__(self):
        self.agents = {
            "data_analyst": AIAgent(
                name="data_analyst",
                port=6001,
                url="http://localhost:6001",
                specialization="Data Analysis & Insights",
                capabilities=[
                    AgentCapability(
                        name="analyze_revenue",
                        description="Analyze revenue patterns and trends",
                        input_schema={"type": "object", "properties": {"timeframe": {"type": "string"}}},
                        output_schema={"type": "object", "properties": {"insights": {"type": "array"}}}
                    ),
                    AgentCapability(
                        name="customer_segmentation", 
                        description="Segment customers based on behavior",
                        input_schema={"type": "object", "properties": {"criteria": {"type": "array"}}},
                        output_schema={"type": "object", "properties": {"segments": {"type": "array"}}}
                    )
                ],
                max_concurrent_tasks=3
            ),
            "automation_specialist": AIAgent(
                name="automation_specialist",
                port=6002,
                url="http://localhost:6002",
                specialization="Process Automation & Workflows",
                capabilities=[
                    AgentCapability(
                        name="create_automation",
                        description="Create automated workflows",
                        input_schema={"type": "object", "properties": {"process": {"type": "string"}}},
                        output_schema={"type": "object", "properties": {"workflow_id": {"type": "string"}}}
                    ),
                    AgentCapability(
                        name="optimize_workflow",
                        description="Optimize existing workflows",
                        input_schema={"type": "object", "properties": {"workflow_id": {"type": "string"}}},
                        output_schema={"type": "object", "properties": {"improvements": {"type": "array"}}}
                    )
                ],
                max_concurrent_tasks=5
            ),
            "content_creator": AIAgent(
                name="content_creator",
                port=6003,
                url="http://localhost:6003",
                specialization="Content Generation & Marketing",
                capabilities=[
                    AgentCapability(
                        name="generate_proposal",
                        description="Generate customer proposals",
                        input_schema={"type": "object", "properties": {"customer_data": {"type": "object"}}},
                        output_schema={"type": "object", "properties": {"proposal": {"type": "string"}}}
                    ),
                    AgentCapability(
                        name="create_marketing_content",
                        description="Create marketing materials",
                        input_schema={"type": "object", "properties": {"campaign_type": {"type": "string"}}},
                        output_schema={"type": "object", "properties": {"content": {"type": "array"}}}
                    )
                ],
                max_concurrent_tasks=4
            ),
            "customer_success": AIAgent(
                name="customer_success",
                port=6004,
                url="http://localhost:6004", 
                specialization="Customer Success & Support",
                capabilities=[
                    AgentCapability(
                        name="analyze_satisfaction",
                        description="Analyze customer satisfaction metrics",
                        input_schema={"type": "object", "properties": {"customer_id": {"type": "string"}}},
                        output_schema={"type": "object", "properties": {"score": {"type": "number"}}}
                    ),
                    AgentCapability(
                        name="generate_support_response",
                        description="Generate customer support responses",
                        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
                        output_schema={"type": "object", "properties": {"response": {"type": "string"}}}
                    )
                ],
                max_concurrent_tasks=6
            ),
            "financial_advisor": AIAgent(
                name="financial_advisor",
                port=6005,
                url="http://localhost:6005",
                specialization="Financial Analysis & Planning",
                capabilities=[
                    AgentCapability(
                        name="forecast_revenue",
                        description="Generate revenue forecasts",
                        input_schema={"type": "object", "properties": {"period": {"type": "string"}}},
                        output_schema={"type": "object", "properties": {"forecast": {"type": "object"}}}
                    ),
                    AgentCapability(
                        name="cost_optimization",
                        description="Analyze and optimize costs",
                        input_schema={"type": "object", "properties": {"department": {"type": "string"}}},
                        output_schema={"type": "object", "properties": {"recommendations": {"type": "array"}}}
                    )
                ],
                max_concurrent_tasks=3
            ),
            "operations_manager": AIAgent(
                name="operations_manager",
                port=6006,
                url="http://localhost:6006",
                specialization="Operations Management & Optimization",
                capabilities=[
                    AgentCapability(
                        name="schedule_optimization",
                        description="Optimize scheduling and resource allocation",
                        input_schema={"type": "object", "properties": {"resources": {"type": "array"}}},
                        output_schema={"type": "object", "properties": {"schedule": {"type": "object"}}}
                    ),
                    AgentCapability(
                        name="performance_analysis",
                        description="Analyze operational performance",
                        input_schema={"type": "object", "properties": {"metrics": {"type": "array"}}},
                        output_schema={"type": "object", "properties": {"analysis": {"type": "object"}}}
                    )
                ],
                max_concurrent_tasks=4
            )
        }
        
        # Task queue for managing workload
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
        self.workflow_executions = {}
        
    async def check_agent_health(self, agent_name: str) -> Dict[str, Any]:
        """Check health of a specific AI agent"""
        if agent_name not in self.agents:
            return {"error": f"Unknown agent: {agent_name}"}
        
        agent = self.agents[agent_name]
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{agent.url}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    agent.status = AgentStatus.HEALTHY
                    agent.current_tasks = health_data.get("active_tasks", 0)
                    agent.last_check = datetime.now()
                    
                    return {
                        "agent": agent_name,
                        "status": "healthy",
                        "response_time": (datetime.now() - start_time).total_seconds(),
                        "specialization": agent.specialization,
                        "capabilities": [cap.name for cap in agent.capabilities],
                        "current_tasks": agent.current_tasks,
                        "max_tasks": agent.max_concurrent_tasks,
                        "availability": agent.max_concurrent_tasks - agent.current_tasks,
                        "url": agent.url
                    }
                else:
                    agent.status = AgentStatus.ERROR
                    return {
                        "agent": agent_name,
                        "status": "error",
                        "error": f"HTTP {response.status_code}"
                    }
                    
        except Exception as e:
            agent.status = AgentStatus.OFFLINE
            logger.error(f"Health check failed for {agent_name}: {e}")
            return {
                "agent": agent_name,
                "status": "offline",
                "error": str(e)
            }
    
    async def check_all_agents(self) -> Dict[str, Any]:
        """Check health of all AI agents"""
        results = {}
        tasks = []
        
        for agent_name in self.agents.keys():
            task = self.check_agent_health(agent_name)
            tasks.append((agent_name, task))
        
        for agent_name, task in tasks:
            results[agent_name] = await task
            
        return {
            "timestamp": datetime.now().isoformat(),
            "agents": results,
            "summary": {
                "total": len(self.agents),
                "healthy": len([r for r in results.values() if r.get("status") == "healthy"]),
                "error": len([r for r in results.values() if r.get("status") == "error"]),
                "offline": len([r for r in results.values() if r.get("status") == "offline"]),
                "total_capacity": sum(agent.max_concurrent_tasks for agent in self.agents.values()),
                "current_load": sum(agent.current_tasks for agent in self.agents.values())
            }
        }
    
    def select_best_agent(self, task_type: str, priority: TaskPriority = TaskPriority.NORMAL) -> Optional[str]:
        """Select the best agent for a task based on capabilities and load"""
        candidates = []
        
        for agent_name, agent in self.agents.items():
            # Check if agent has required capability
            has_capability = any(cap.name == task_type for cap in agent.capabilities)
            if not has_capability:
                continue
                
            # Check if agent is available
            if agent.status != AgentStatus.HEALTHY:
                continue
                
            # Check if agent has capacity
            if agent.current_tasks >= agent.max_concurrent_tasks:
                continue
                
            # Calculate score based on availability and performance
            availability_score = (agent.max_concurrent_tasks - agent.current_tasks) / agent.max_concurrent_tasks
            performance_score = agent.performance_metrics.get(task_type, 0.5)
            
            total_score = availability_score * 0.6 + performance_score * 0.4
            
            candidates.append((agent_name, total_score))
        
        if not candidates:
            return None
            
        # Sort by score and return best candidate
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    async def delegate_task(self, request: TaskRequest) -> TaskResponse:
        """Delegate a task to an AI agent"""
        import uuid
        task_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        # Select agent if not specified
        if not request.agent_name:
            request.agent_name = self.select_best_agent(request.task_type, request.priority)
            
        if not request.agent_name:
            return TaskResponse(
                task_id=task_id,
                agent_name="none",
                success=False,
                error="No available agent found for this task type",
                execution_time=0.0,
                timestamp=datetime.now()
            )
        
        if request.agent_name not in self.agents:
            return TaskResponse(
                task_id=task_id,
                agent_name=request.agent_name,
                success=False,
                error=f"Unknown agent: {request.agent_name}",
                execution_time=0.0,
                timestamp=datetime.now()
            )
        
        agent = self.agents[request.agent_name]
        
        try:
            async with httpx.AsyncClient(timeout=request.timeout) as client:
                payload = {
                    "task_id": task_id,
                    "task_type": request.task_type,
                    "priority": request.priority.value,
                    "context": request.context,
                    "callback_url": request.callback_url
                }
                
                response = await client.post(
                    f"{agent.url}/execute",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    result_data = response.json()
                    
                    # Update agent task count
                    agent.current_tasks = max(0, agent.current_tasks - 1)
                    
                    # Update performance metrics
                    if request.task_type not in agent.performance_metrics:
                        agent.performance_metrics[request.task_type] = 0.5
                    
                    # Update performance based on execution time (simple heuristic)
                    if execution_time < 10:  # Fast execution
                        agent.performance_metrics[request.task_type] = min(1.0, 
                            agent.performance_metrics[request.task_type] + 0.1)
                    elif execution_time > 60:  # Slow execution
                        agent.performance_metrics[request.task_type] = max(0.1,
                            agent.performance_metrics[request.task_type] - 0.1)
                    
                    return TaskResponse(
                        task_id=task_id,
                        agent_name=request.agent_name,
                        success=True,
                        result=result_data.get("result"),
                        execution_time=execution_time,
                        timestamp=datetime.now(),
                        metadata=result_data.get("metadata", {})
                    )
                else:
                    agent.current_tasks = max(0, agent.current_tasks - 1)
                    return TaskResponse(
                        task_id=task_id,
                        agent_name=request.agent_name,
                        success=False,
                        error=f"HTTP {response.status_code}: {response.text}",
                        execution_time=execution_time,
                        timestamp=datetime.now()
                    )
                    
        except Exception as e:
            agent.current_tasks = max(0, agent.current_tasks - 1)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Task delegation failed to {request.agent_name}: {e}")
            return TaskResponse(
                task_id=task_id,
                agent_name=request.agent_name,
                success=False,
                error=str(e),
                execution_time=execution_time,
                timestamp=datetime.now()
            )
    
    async def execute_workflow(self, workflow: WorkflowRequest) -> Dict[str, Any]:
        """Execute a multi-step workflow"""
        workflow_id = workflow.workflow_id
        start_time = datetime.now()
        
        # Initialize workflow execution tracking
        self.workflow_executions[workflow_id] = {
            "name": workflow.name,
            "description": workflow.description,
            "status": "running",
            "steps": {},
            "completed_steps": [],
            "failed_steps": [],
            "start_time": start_time,
            "current_step": None
        }
        
        execution = self.workflow_executions[workflow_id]
        
        try:
            # Build dependency graph
            step_dependencies = {step.step_id: step.depends_on for step in workflow.steps}
            step_map = {step.step_id: step for step in workflow.steps}
            
            # Execute steps in dependency order
            completed_steps = set()
            
            while len(completed_steps) < len(workflow.steps):
                # Find steps that can be executed (dependencies satisfied)
                ready_steps = []
                for step in workflow.steps:
                    if (step.step_id not in completed_steps and 
                        all(dep in completed_steps for dep in step.depends_on)):
                        ready_steps.append(step)
                
                if not ready_steps:
                    # Check if we have a circular dependency or other issue
                    remaining_steps = [s for s in workflow.steps if s.step_id not in completed_steps]
                    execution["status"] = "failed"
                    execution["error"] = f"Cannot execute remaining steps: {[s.step_id for s in remaining_steps]}"
                    break
                
                # Execute ready steps (can be done in parallel)
                step_tasks = []
                for step in ready_steps:
                    task_request = TaskRequest(
                        agent_name=step.agent_name,
                        task_type=step.task_type,
                        context=step.context,
                        timeout=step.timeout
                    )
                    step_tasks.append((step.step_id, self.delegate_task(task_request)))
                
                # Wait for all ready steps to complete
                for step_id, task in step_tasks:
                    execution["current_step"] = step_id
                    result = await task
                    
                    execution["steps"][step_id] = {
                        "agent": result.agent_name,
                        "success": result.success,
                        "result": result.result,
                        "error": result.error,
                        "execution_time": result.execution_time,
                        "timestamp": result.timestamp.isoformat()
                    }
                    
                    if result.success:
                        completed_steps.add(step_id)
                        execution["completed_steps"].append(step_id)
                    else:
                        execution["failed_steps"].append(step_id)
                        
                        if not workflow.auto_retry:
                            execution["status"] = "failed"
                            execution["error"] = f"Step {step_id} failed: {result.error}"
                            break
            
            # Determine final status
            if execution["status"] != "failed":
                if len(completed_steps) == len(workflow.steps):
                    execution["status"] = "completed"
                else:
                    execution["status"] = "partially_completed"
            
            execution["end_time"] = datetime.now()
            execution["total_execution_time"] = (execution["end_time"] - start_time).total_seconds()
            execution["current_step"] = None
            
            return {
                "workflow_id": workflow_id,
                "status": execution["status"],
                "completed_steps": len(execution["completed_steps"]),
                "failed_steps": len(execution["failed_steps"]),
                "total_steps": len(workflow.steps),
                "execution_time": execution["total_execution_time"],
                "details": execution
            }
            
        except Exception as e:
            execution["status"] = "error"
            execution["error"] = str(e)
            execution["end_time"] = datetime.now()
            logger.error(f"Workflow execution failed: {e}")
            
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "error": str(e),
                "details": execution
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current status of all agents"""
        return {
            "agents": {
                name: {
                    "name": agent.name,
                    "port": agent.port,
                    "url": agent.url,
                    "specialization": agent.specialization,
                    "status": agent.status.value,
                    "current_tasks": agent.current_tasks,
                    "max_tasks": agent.max_concurrent_tasks,
                    "capabilities": [cap.name for cap in agent.capabilities],
                    "performance_metrics": agent.performance_metrics,
                    "last_check": agent.last_check.isoformat() if agent.last_check else None
                }
                for name, agent in self.agents.items()
            },
            "active_workflows": len(self.workflow_executions),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific workflow"""
        if workflow_id not in self.workflow_executions:
            return None
        
        execution = self.workflow_executions[workflow_id]
        return {
            "workflow_id": workflow_id,
            "name": execution["name"],
            "status": execution["status"],
            "current_step": execution["current_step"],
            "completed_steps": len(execution["completed_steps"]),
            "failed_steps": len(execution["failed_steps"]),
            "start_time": execution["start_time"].isoformat(),
            "steps": execution["steps"]
        }

# Global AI agent service instance  
ai_agent_service = AIAgentService()