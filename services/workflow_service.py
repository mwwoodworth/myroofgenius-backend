"""
Workflow Orchestration Service - Complex Multi-Step Task Management
Combines MCP operations and AI agent tasks into sophisticated workflows
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pydantic import BaseModel
from enum import Enum
import uuid

from services.mcp_service import mcp_service, MCPRequest
from services.ai_agent_service import ai_agent_service, TaskRequest, TaskPriority

logger = logging.getLogger(__name__)

class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepType(str, Enum):
    """Types of workflow steps"""
    MCP_CALL = "mcp_call"
    AI_TASK = "ai_task"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    DELAY = "delay"
    WEBHOOK = "webhook"

class ConditionOperator(str, Enum):
    """Condition operators for workflow logic"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"

class WorkflowStep(BaseModel):
    """Individual step in a workflow"""
    step_id: str
    name: str
    step_type: StepType
    config: Dict[str, Any] = {}
    depends_on: List[str] = []
    timeout: int = 300
    retry_count: int = 0
    max_retries: int = 3
    on_failure: Optional[str] = None  # Step ID to execute on failure
    conditions: List[Dict[str, Any]] = []  # Conditions for conditional execution

class WorkflowTemplate(BaseModel):
    """Reusable workflow template"""
    template_id: str
    name: str
    description: str
    category: str
    parameters: List[Dict[str, Any]] = []
    steps: List[WorkflowStep]
    tags: List[str] = []

class WorkflowExecution(BaseModel):
    """Workflow execution instance"""
    execution_id: str
    workflow_id: str
    name: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    input_data: Dict[str, Any] = {}
    output_data: Dict[str, Any] = {}
    current_step: Optional[str] = None
    completed_steps: List[str] = []
    failed_steps: List[str] = []
    step_results: Dict[str, Any] = {}
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None

class WorkflowService:
    """Service for orchestrating complex workflows"""
    
    def __init__(self):
        self.templates = {}
        self.executions = {}
        self.load_default_templates()
    
    def load_default_templates(self):
        """Load default workflow templates"""
        
        # Customer Onboarding Workflow
        customer_onboarding = WorkflowTemplate(
            template_id="customer_onboarding",
            name="Customer Onboarding",
            description="Complete customer onboarding process with AI assistance",
            category="customer_management",
            parameters=[
                {"name": "customer_data", "type": "object", "required": True},
                {"name": "subscription_tier", "type": "string", "required": True}
            ],
            steps=[
                WorkflowStep(
                    step_id="validate_data",
                    name="Validate Customer Data",
                    step_type=StepType.AI_TASK,
                    config={
                        "agent_name": "data_analyst",
                        "task_type": "validate_customer_data",
                        "context": {"data": "{{customer_data}}"}
                    }
                ),
                WorkflowStep(
                    step_id="create_database_record",
                    name="Create Database Record",
                    step_type=StepType.MCP_CALL,
                    config={
                        "server": "postgres",
                        "method": "execute",
                        "params": {
                            "query": "INSERT INTO customers (name, email, subscription_tier) VALUES (%(name)s, %(email)s, %(tier)s)",
                            "params": {
                                "name": "{{customer_data.name}}",
                                "email": "{{customer_data.email}}",
                                "tier": "{{subscription_tier}}"
                            }
                        }
                    },
                    depends_on=["validate_data"]
                ),
                WorkflowStep(
                    step_id="generate_welcome_content",
                    name="Generate Welcome Content",
                    step_type=StepType.AI_TASK,
                    config={
                        "agent_name": "content_creator",
                        "task_type": "generate_welcome_email",
                        "context": {
                            "customer_name": "{{customer_data.name}}",
                            "subscription_tier": "{{subscription_tier}}"
                        }
                    },
                    depends_on=["create_database_record"]
                ),
                WorkflowStep(
                    step_id="send_welcome_email",
                    name="Send Welcome Email",
                    step_type=StepType.MCP_CALL,
                    config={
                        "server": "automation",
                        "method": "send_email",
                        "params": {
                            "to": "{{customer_data.email}}",
                            "subject": "Welcome to MyRoofGenius!",
                            "content": "{{generate_welcome_content.result}}"
                        }
                    },
                    depends_on=["generate_welcome_content"]
                ),
                WorkflowStep(
                    step_id="schedule_followup",
                    name="Schedule Follow-up",
                    step_type=StepType.AI_TASK,
                    config={
                        "agent_name": "customer_success",
                        "task_type": "schedule_followup",
                        "context": {
                            "customer_id": "{{create_database_record.result.customer_id}}",
                            "followup_days": 3
                        }
                    },
                    depends_on=["send_welcome_email"]
                )
            ],
            tags=["customer", "onboarding", "automation"]
        )
        
        # Revenue Analysis Workflow
        revenue_analysis = WorkflowTemplate(
            template_id="revenue_analysis",
            name="Comprehensive Revenue Analysis",
            description="Multi-step revenue analysis with AI insights and reporting",
            category="analytics",
            parameters=[
                {"name": "timeframe", "type": "string", "default": "30d"},
                {"name": "include_forecasts", "type": "boolean", "default": True}
            ],
            steps=[
                WorkflowStep(
                    step_id="fetch_revenue_data",
                    name="Fetch Revenue Data",
                    step_type=StepType.MCP_CALL,
                    config={
                        "server": "postgres",
                        "method": "query",
                        "params": {
                            "query": "SELECT * FROM revenue_transactions WHERE created_at >= NOW() - INTERVAL '{{timeframe}}'"
                        }
                    }
                ),
                WorkflowStep(
                    step_id="analyze_patterns",
                    name="Analyze Revenue Patterns",
                    step_type=StepType.AI_TASK,
                    config={
                        "agent_name": "data_analyst",
                        "task_type": "analyze_revenue",
                        "context": {
                            "data": "{{fetch_revenue_data.result}}",
                            "timeframe": "{{timeframe}}"
                        }
                    },
                    depends_on=["fetch_revenue_data"]
                ),
                WorkflowStep(
                    step_id="generate_forecast",
                    name="Generate Revenue Forecast",
                    step_type=StepType.AI_TASK,
                    config={
                        "agent_name": "financial_advisor",
                        "task_type": "forecast_revenue",
                        "context": {
                            "historical_data": "{{fetch_revenue_data.result}}",
                            "analysis": "{{analyze_patterns.result}}"
                        }
                    },
                    depends_on=["analyze_patterns"],
                    conditions=[
                        {"field": "include_forecasts", "operator": "is_true"}
                    ]
                ),
                WorkflowStep(
                    step_id="create_report",
                    name="Create Analysis Report",
                    step_type=StepType.AI_TASK,
                    config={
                        "agent_name": "content_creator",
                        "task_type": "create_revenue_report",
                        "context": {
                            "analysis": "{{analyze_patterns.result}}",
                            "forecast": "{{generate_forecast.result}}",
                            "timeframe": "{{timeframe}}"
                        }
                    },
                    depends_on=["analyze_patterns", "generate_forecast"]
                ),
                WorkflowStep(
                    step_id="store_report",
                    name="Store Report",
                    step_type=StepType.MCP_CALL,
                    config={
                        "server": "filesystem",
                        "method": "write_file",
                        "params": {
                            "path": "/reports/revenue_analysis_{{execution_id}}.json",
                            "content": "{{create_report.result}}"
                        }
                    },
                    depends_on=["create_report"]
                )
            ],
            tags=["revenue", "analytics", "reporting"]
        )
        
        # Customer Support Workflow
        customer_support = WorkflowTemplate(
            template_id="customer_support",
            name="Intelligent Customer Support",
            description="AI-powered customer support with escalation handling",
            category="customer_service",
            parameters=[
                {"name": "customer_query", "type": "string", "required": True},
                {"name": "customer_id", "type": "string", "required": True},
                {"name": "priority", "type": "string", "default": "normal"}
            ],
            steps=[
                WorkflowStep(
                    step_id="fetch_customer_context",
                    name="Fetch Customer Context",
                    step_type=StepType.MCP_CALL,
                    config={
                        "server": "postgres",
                        "method": "query",
                        "params": {
                            "query": "SELECT * FROM customers WHERE id = %(customer_id)s",
                            "params": {"customer_id": "{{customer_id}}"}
                        }
                    }
                ),
                WorkflowStep(
                    step_id="analyze_query",
                    name="Analyze Customer Query",
                    step_type=StepType.AI_TASK,
                    config={
                        "agent_name": "customer_success",
                        "task_type": "analyze_support_query",
                        "context": {
                            "query": "{{customer_query}}",
                            "customer_data": "{{fetch_customer_context.result}}"
                        }
                    },
                    depends_on=["fetch_customer_context"]
                ),
                WorkflowStep(
                    step_id="generate_response",
                    name="Generate Response",
                    step_type=StepType.AI_TASK,
                    config={
                        "agent_name": "customer_success",
                        "task_type": "generate_support_response",
                        "context": {
                            "query": "{{customer_query}}",
                            "analysis": "{{analyze_query.result}}",
                            "customer_data": "{{fetch_customer_context.result}}"
                        }
                    },
                    depends_on=["analyze_query"]
                ),
                WorkflowStep(
                    step_id="check_escalation",
                    name="Check if Escalation Needed",
                    step_type=StepType.CONDITION,
                    config={
                        "conditions": [
                            {"field": "analyze_query.result.complexity", "operator": "greater_than", "value": 0.8},
                            {"field": "priority", "operator": "equals", "value": "urgent"}
                        ],
                        "logic": "or"
                    },
                    depends_on=["analyze_query"]
                ),
                WorkflowStep(
                    step_id="escalate_to_human",
                    name="Escalate to Human Agent",
                    step_type=StepType.MCP_CALL,
                    config={
                        "server": "automation",
                        "method": "create_ticket",
                        "params": {
                            "customer_id": "{{customer_id}}",
                            "query": "{{customer_query}}",
                            "analysis": "{{analyze_query.result}}",
                            "priority": "high"
                        }
                    },
                    depends_on=["check_escalation"],
                    conditions=[
                        {"field": "check_escalation.result", "operator": "is_true"}
                    ]
                ),
                WorkflowStep(
                    step_id="log_interaction",
                    name="Log Customer Interaction",
                    step_type=StepType.MCP_CALL,
                    config={
                        "server": "postgres",
                        "method": "execute",
                        "params": {
                            "query": "INSERT INTO customer_interactions (customer_id, query, response, escalated) VALUES (%(customer_id)s, %(query)s, %(response)s, %(escalated)s)",
                            "params": {
                                "customer_id": "{{customer_id}}",
                                "query": "{{customer_query}}",
                                "response": "{{generate_response.result}}",
                                "escalated": "{{check_escalation.result}}"
                            }
                        }
                    },
                    depends_on=["generate_response", "check_escalation"]
                )
            ],
            tags=["support", "customer", "ai"]
        )
        
        # Store templates
        self.templates[customer_onboarding.template_id] = customer_onboarding
        self.templates[revenue_analysis.template_id] = revenue_analysis
        self.templates[customer_support.template_id] = customer_support
    
    def get_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available workflow templates"""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return [
            {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "parameters": t.parameters,
                "steps_count": len(t.steps),
                "tags": t.tags
            }
            for t in templates
        ]
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get a specific workflow template"""
        return self.templates.get(template_id)
    
    async def start_workflow(self, template_id: str, input_data: Dict[str, Any]) -> str:
        """Start a new workflow execution"""
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        execution_id = str(uuid.uuid4())
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=template_id,
            name=template.name,
            input_data=input_data,
            created_at=datetime.now()
        )
        
        self.executions[execution_id] = execution
        
        # Start execution in background
        asyncio.create_task(self._execute_workflow(execution_id))
        
        return execution_id
    
    async def _execute_workflow(self, execution_id: str):
        """Execute a workflow"""
        execution = self.executions[execution_id]
        template = self.templates[execution.workflow_id]
        
        try:
            execution.status = WorkflowStatus.RUNNING
            execution.started_at = datetime.now()
            
            # Build step dependency graph
            step_map = {step.step_id: step for step in template.steps}
            completed_steps = set()
            context = {"input": execution.input_data}
            
            while len(completed_steps) < len(template.steps):
                # Find ready steps
                ready_steps = []
                for step in template.steps:
                    if (step.step_id not in completed_steps and
                        step.step_id not in execution.failed_steps and
                        all(dep in completed_steps for dep in step.depends_on)):
                        
                        # Check conditions
                        if self._check_conditions(step, context):
                            ready_steps.append(step)
                
                if not ready_steps:
                    # Check if we're done or have issues
                    remaining_steps = [s for s in template.steps if s.step_id not in completed_steps]
                    if remaining_steps and not execution.failed_steps:
                        execution.status = WorkflowStatus.FAILED
                        execution.error_message = "No ready steps found - possible circular dependency"
                        break
                    else:
                        break  # All possible steps completed
                
                # Execute ready steps
                for step in ready_steps:
                    execution.current_step = step.step_id
                    
                    try:
                        result = await self._execute_step(step, context)
                        execution.step_results[step.step_id] = result
                        completed_steps.add(step.step_id)
                        execution.completed_steps.append(step.step_id)
                        
                        # Update context with step result
                        context[step.step_id] = result
                        
                    except Exception as e:
                        logger.error(f"Step {step.step_id} failed: {e}")
                        execution.failed_steps.append(step.step_id)
                        execution.step_results[step.step_id] = {"error": str(e)}
                        
                        # Handle failure action
                        if step.on_failure and step.on_failure in step_map:
                            failure_step = step_map[step.on_failure]
                            try:
                                failure_result = await self._execute_step(failure_step, context)
                                execution.step_results[failure_step.step_id] = failure_result
                            except Exception as fe:
                                logger.error(f"Failure handler {step.on_failure} also failed: {fe}")
                        
                        # Continue or stop based on criticality
                        if step.step_id in ["validate_data", "create_database_record"]:  # Critical steps
                            execution.status = WorkflowStatus.FAILED
                            execution.error_message = f"Critical step {step.step_id} failed: {e}"
                            break
            
            # Determine final status
            if execution.status == WorkflowStatus.RUNNING:
                if execution.failed_steps:
                    execution.status = WorkflowStatus.COMPLETED if len(execution.completed_steps) > len(execution.failed_steps) else WorkflowStatus.FAILED
                else:
                    execution.status = WorkflowStatus.COMPLETED
            
            execution.completed_at = datetime.now()
            execution.current_step = None
            
            if execution.started_at:
                execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()
            
            # Store final output
            execution.output_data = {
                "completed_steps": execution.completed_steps,
                "failed_steps": execution.failed_steps,
                "step_results": execution.step_results,
                "execution_time": execution.execution_time
            }
            
            logger.info(f"Workflow {execution_id} completed with status: {execution.status}")
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            execution.current_step = None
            logger.error(f"Workflow {execution_id} failed: {e}")
    
    async def _execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Any:
        """Execute a single workflow step"""
        config = self._interpolate_config(step.config, context)
        
        if step.step_type == StepType.MCP_CALL:
            return await self._execute_mcp_step(config)
        elif step.step_type == StepType.AI_TASK:
            return await self._execute_ai_step(config)
        elif step.step_type == StepType.CONDITION:
            return self._execute_condition_step(config, context)
        elif step.step_type == StepType.DELAY:
            await asyncio.sleep(config.get("seconds", 1))
            return {"delayed": config.get("seconds", 1)}
        elif step.step_type == StepType.WEBHOOK:
            return await self._execute_webhook_step(config)
        else:
            raise ValueError(f"Unknown step type: {step.step_type}")
    
    async def _execute_mcp_step(self, config: Dict[str, Any]) -> Any:
        """Execute an MCP step"""
        request = MCPRequest(
            server=config["server"],
            method=config["method"],
            params=config.get("params", {}),
            timeout=config.get("timeout", 300)
        )
        
        response = await mcp_service.call_mcp_server(request)
        
        if not response.success:
            raise Exception(f"MCP call failed: {response.error}")
        
        return response.data
    
    async def _execute_ai_step(self, config: Dict[str, Any]) -> Any:
        """Execute an AI task step"""
        request = TaskRequest(
            agent_name=config.get("agent_name"),
            task_type=config["task_type"],
            context=config.get("context", {}),
            priority=TaskPriority(config.get("priority", "normal")),
            timeout=config.get("timeout", 300)
        )
        
        response = await ai_agent_service.delegate_task(request)
        
        if not response.success:
            raise Exception(f"AI task failed: {response.error}")
        
        return response.result
    
    def _execute_condition_step(self, config: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Execute a condition step"""
        conditions = config.get("conditions", [])
        logic = config.get("logic", "and")  # "and" or "or"
        
        results = []
        for condition in conditions:
            field_path = condition["field"]
            operator = condition["operator"]
            expected_value = condition.get("value")
            
            # Get actual value from context
            actual_value = self._get_nested_value(context, field_path)
            
            # Evaluate condition
            if operator == ConditionOperator.EQUALS:
                result = actual_value == expected_value
            elif operator == ConditionOperator.NOT_EQUALS:
                result = actual_value != expected_value
            elif operator == ConditionOperator.GREATER_THAN:
                result = actual_value > expected_value
            elif operator == ConditionOperator.LESS_THAN:
                result = actual_value < expected_value
            elif operator == ConditionOperator.CONTAINS:
                result = expected_value in str(actual_value)
            elif operator == ConditionOperator.IS_TRUE:
                result = bool(actual_value)
            elif operator == ConditionOperator.IS_FALSE:
                result = not bool(actual_value)
            else:
                result = False
            
            results.append(result)
        
        # Apply logic
        if logic == "or":
            return any(results)
        else:  # "and"
            return all(results)
    
    async def _execute_webhook_step(self, config: Dict[str, Any]) -> Any:
        """Execute a webhook step"""
        import httpx
        
        url = config["url"]
        method = config.get("method", "POST")
        headers = config.get("headers", {})
        data = config.get("data", {})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "POST":
                response = await client.post(url, json=data, headers=headers)
            elif method.upper() == "GET":
                response = await client.get(url, params=data, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code >= 400:
                raise Exception(f"Webhook failed: {response.status_code} {response.text}")
            
            try:
                return response.json()
            except:
                return {"status_code": response.status_code, "text": response.text}
    
    def _interpolate_config(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Interpolate template variables in config"""
        config_str = json.dumps(config)
        
        # Simple template replacement
        for key, value in context.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    config_str = config_str.replace(f"{{{{{key}.{subkey}}}}}", str(subvalue))
            else:
                config_str = config_str.replace(f"{{{{{key}}}}}", str(value))
        
        return json.loads(config_str)
    
    def _check_conditions(self, step: WorkflowStep, context: Dict[str, Any]) -> bool:
        """Check if step conditions are met"""
        if not step.conditions:
            return True
        
        for condition in step.conditions:
            field_path = condition["field"]
            operator = condition["operator"]
            expected_value = condition.get("value")
            
            actual_value = self._get_nested_value(context, field_path)
            
            if operator == "is_true" and not actual_value:
                return False
            elif operator == "is_false" and actual_value:
                return False
            elif operator == "equals" and actual_value != expected_value:
                return False
        
        return True
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from data using dot notation"""
        keys = path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        execution = self.executions.get(execution_id)
        if not execution:
            return None
        
        return {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "name": execution.name,
            "status": execution.status.value,
            "current_step": execution.current_step,
            "completed_steps": len(execution.completed_steps),
            "failed_steps": len(execution.failed_steps),
            "total_steps": len(self.templates[execution.workflow_id].steps),
            "created_at": execution.created_at.isoformat(),
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "execution_time": execution.execution_time,
            "error_message": execution.error_message,
            "step_results": execution.step_results
        }
    
    def get_executions(self, status: Optional[WorkflowStatus] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get workflow executions"""
        executions = list(self.executions.values())
        
        if status:
            executions = [e for e in executions if e.status == status]
        
        # Sort by creation time, most recent first
        executions.sort(key=lambda x: x.created_at, reverse=True)
        
        return [
            {
                "execution_id": e.execution_id,
                "workflow_id": e.workflow_id,
                "name": e.name,
                "status": e.status.value,
                "created_at": e.created_at.isoformat(),
                "execution_time": e.execution_time
            }
            for e in executions[:limit]
        ]
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow"""
        execution = self.executions.get(execution_id)
        if not execution:
            return False
        
        if execution.status in [WorkflowStatus.RUNNING, WorkflowStatus.PENDING]:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now()
            execution.current_step = None
            return True
        
        return False

# Global workflow service instance
workflow_service = WorkflowService()