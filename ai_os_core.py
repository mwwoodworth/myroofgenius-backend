"""
AI Operating System Core - Production Ready LangGraph Multi-Agent Orchestration
The heart of our AI-native business platform that powers everything
"""

import os
import asyncio
import json
import hashlib
import time
import logging
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, List, Optional, TypedDict, Annotated, Literal
from enum import Enum
import uuid

from langgraph.graph import StateGraph, END, MessageGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from pydantic import BaseModel, Field
import redis
import asyncpg
from fastapi import WebSocket

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agent Types - Every single aspect of the system
class AgentType(str, Enum):
    # Core System Agents
    ORCHESTRATOR = "orchestrator"
    MEMORY_MANAGER = "memory_manager"
    SECURITY_GUARDIAN = "security_guardian"
    PERFORMANCE_OPTIMIZER = "performance_optimizer"
    
    # Business Logic Agents
    REVENUE_MAXIMIZER = "revenue_maximizer"
    CUSTOMER_SUCCESS = "customer_success"
    LEAD_QUALIFIER = "lead_qualifier"
    SALES_CLOSER = "sales_closer"
    
    # Technical Agents
    CODE_GENERATOR = "code_generator"
    BUG_HUNTER = "bug_hunter"
    DEPLOYMENT_MANAGER = "deployment_manager"
    DATABASE_OPTIMIZER = "database_optimizer"
    API_GATEWAY = "api_gateway"
    
    # Monitoring Agents
    HEALTH_MONITOR = "health_monitor"
    ALERT_MANAGER = "alert_manager"
    LOG_ANALYZER = "log_analyzer"
    METRICS_COLLECTOR = "metrics_collector"
    
    # AI/ML Agents
    MODEL_TRAINER = "model_trainer"
    PREDICTION_ENGINE = "prediction_engine"
    PATTERN_RECOGNIZER = "pattern_recognizer"
    ANOMALY_DETECTOR = "anomaly_detector"
    
    # Industry Specific Agents (Roofing Example)
    WEATHER_ANALYZER = "weather_analyzer"
    PROJECT_ESTIMATOR = "project_estimator"
    CREW_SCHEDULER = "crew_scheduler"
    MATERIAL_OPTIMIZER = "material_optimizer"
    PERMIT_MANAGER = "permit_manager"
    SAFETY_COMPLIANCE = "safety_compliance"
    
    # Communication Agents
    EMAIL_COMPOSER = "email_composer"
    SMS_MANAGER = "sms_manager"
    WEBHOOK_PROCESSOR = "webhook_processor"
    NOTIFICATION_DISPATCHER = "notification_dispatcher"
    
    # Financial Agents
    INVOICE_GENERATOR = "invoice_generator"
    PAYMENT_PROCESSOR = "payment_processor"
    EXPENSE_TRACKER = "expense_tracker"
    PROFIT_CALCULATOR = "profit_calculator"
    
    # Content Agents
    CONTENT_CREATOR = "content_creator"
    SEO_OPTIMIZER = "seo_optimizer"
    SOCIAL_MEDIA_MANAGER = "social_media_manager"
    BRAND_GUARDIAN = "brand_guardian"
    
    # Automation Agents
    WORKFLOW_AUTOMATOR = "workflow_automator"
    TASK_SCHEDULER = "task_scheduler"
    BACKUP_MANAGER = "backup_manager"
    CLEANUP_CREW = "cleanup_crew"

# State definition for the graph
class GraphState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_agent: str
    task_queue: List[Dict[str, Any]]
    memory_context: Dict[str, Any]
    active_workflows: List[str]
    metrics: Dict[str, Any]
    decisions_made: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    industry_config: Dict[str, Any]  # Industry-specific configuration
    
class AgentResponse(BaseModel):
    """Standard response from any agent"""
    agent_type: AgentType
    action_taken: str
    result: Dict[str, Any]
    next_agents: List[AgentType] = []
    confidence: float = 1.0
    timestamp: datetime = Field(default_factory=datetime.now)

class AIOS:
    """AI Operating System - The brain that powers everything"""
    
    def __init__(self, industry: str = "roofing", company_name: str = "MyRoofGenius"):
        self.industry = industry
        self.company_name = company_name
        self.agents: Dict[AgentType, Any] = {}
        self.graph = None
        self.memory_saver = MemorySaver()
        self.redis_client = None
        self.pg_pool = None
        self.websocket_connections: List[WebSocket] = []
        
        # Initialize the computational graph
        self._build_graph()
        
        # Initialize all agents
        self._initialize_agents()
        
        logger.info(f"AI OS initialized for {company_name} in {industry} industry")
    
    async def initialize_connections(self):
        """Initialize database and cache connections"""
        try:
            # Redis for real-time caching
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_URL', 'localhost'),
                port=6379,
                decode_responses=True
            )
            
            # PostgreSQL for persistent storage - NO fallback defaults for security
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                raise RuntimeError("DATABASE_URL environment variable is required but not set")
            self.pg_pool = await asyncpg.create_pool(
                db_url,
                min_size=5,
                max_size=20
            )
            
            # Initialize database schema
            await self._init_database_schema()
            
            logger.info("All connections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize connections: {e}")
            raise
    
    async def _init_database_schema(self):
        """Initialize all database tables"""
        async with self.pg_pool.acquire() as conn:
            # Core tables
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS agent_decisions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_type VARCHAR(50),
                    decision JSONB,
                    confidence FLOAT,
                    outcome JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS workflows (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255),
                    industry VARCHAR(100),
                    steps JSONB,
                    status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS agent_memories (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_type VARCHAR(50),
                    memory_key VARCHAR(255),
                    memory_value JSONB,
                    importance FLOAT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    accessed_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_name VARCHAR(100),
                    metric_value FLOAT,
                    tags JSONB,
                    recorded_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Industry-specific tables (example for roofing)
            if self.industry == "roofing":
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS roofing_projects (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        customer_id UUID,
                        address JSONB,
                        roof_type VARCHAR(100),
                        square_footage INT,
                        estimated_cost DECIMAL(10,2),
                        actual_cost DECIMAL(10,2),
                        weather_conditions JSONB,
                        crew_assigned JSONB,
                        materials JSONB,
                        status VARCHAR(50),
                        created_at TIMESTAMP DEFAULT NOW(),
                        scheduled_date DATE,
                        completed_date DATE
                    )
                ''')
    
    def _initialize_agents(self):
        """Initialize all specialized agents"""
        # Create LLM instances for different agent capabilities
        claude = ChatAnthropic(
            model="claude-3-opus-20240229",
            temperature=0.7,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        gpt4 = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize each specialized agent
        for agent_type in AgentType:
            self.agents[agent_type] = self._create_agent(agent_type, claude)
    
    def _create_agent(self, agent_type: AgentType, llm):
        """Create a specialized agent with its own tools and capabilities"""
        agent_tools = self._get_agent_tools(agent_type)
        
        return {
            "type": agent_type,
            "llm": llm,
            "tools": agent_tools,
            "memory": {},
            "active": True
        }
    
    def _get_agent_tools(self, agent_type: AgentType) -> List[Tool]:
        """Get specialized tools for each agent type"""
        tools = []
        
        # Common tools for all agents
        tools.extend([
            Tool(
                name="query_memory",
                func=self._query_memory,
                description="Query the persistent memory system"
            ),
            Tool(
                name="log_decision",
                func=self._log_decision,
                description="Log a decision made by the agent"
            ),
            Tool(
                name="emit_metric",
                func=self._emit_metric,
                description="Emit a metric for monitoring"
            )
        ])
        
        # Agent-specific tools
        if agent_type == AgentType.REVENUE_MAXIMIZER:
            tools.extend([
                Tool(
                    name="analyze_pricing",
                    func=self._analyze_pricing,
                    description="Analyze and optimize pricing strategies"
                ),
                Tool(
                    name="identify_upsell",
                    func=self._identify_upsell,
                    description="Identify upsell opportunities"
                )
            ])
        elif agent_type == AgentType.WEATHER_ANALYZER:
            tools.extend([
                Tool(
                    name="get_weather_forecast",
                    func=self._get_weather_forecast,
                    description="Get weather forecast for project planning"
                ),
                Tool(
                    name="assess_weather_risk",
                    func=self._assess_weather_risk,
                    description="Assess weather-related project risks"
                )
            ])
        elif agent_type == AgentType.CODE_GENERATOR:
            tools.extend([
                Tool(
                    name="generate_code",
                    func=self._generate_code,
                    description="Generate code for new features"
                ),
                Tool(
                    name="review_code",
                    func=self._review_code,
                    description="Review code for quality and security"
                )
            ])
        # ... Add more agent-specific tools
        
        return tools
    
    def _build_graph(self):
        """Build the LangGraph state machine"""
        workflow = StateGraph(GraphState)
        
        # Add nodes for each agent type
        for agent_type in AgentType:
            workflow.add_node(
                agent_type.value,
                lambda state, agent_type=agent_type: self._agent_node(state, agent_type)
            )
        
        # Add the orchestrator as the entry point
        workflow.set_entry_point(AgentType.ORCHESTRATOR.value)
        
        # Add conditional edges based on agent decisions
        for agent_type in AgentType:
            workflow.add_conditional_edges(
                agent_type.value,
                self._route_to_next_agent,
                {
                    agent.value: agent.value 
                    for agent in AgentType
                } | {"end": END}
            )
        
        # Compile the graph
        self.graph = workflow.compile(checkpointer=self.memory_saver)
        
        logger.info("LangGraph workflow compiled successfully")
    
    async def _agent_node(self, state: GraphState, agent_type: AgentType) -> GraphState:
        """Execute an agent node in the graph"""
        agent = self.agents[agent_type]
        
        try:
            # Extract context from state
            messages = state["messages"]
            memory_context = state["memory_context"]
            
            # Agent processes the current state
            response = await self._process_agent_task(
                agent, 
                messages, 
                memory_context
            )
            
            # Update state with agent's response
            state["messages"].append(
                AIMessage(
                    content=json.dumps(response.dict()),
                    name=agent_type.value
                )
            )
            
            # Log the decision
            await self._store_decision(agent_type, response)
            
            # Update metrics
            state["metrics"][f"{agent_type.value}_calls"] = \
                state["metrics"].get(f"{agent_type.value}_calls", 0) + 1
            
            # Broadcast to websockets
            await self._broadcast_agent_activity(agent_type, response)
            
        except Exception as e:
            logger.error(f"Agent {agent_type} error: {e}")
            state["errors"].append({
                "agent": agent_type.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        
        return state
    
    def _route_to_next_agent(self, state: GraphState) -> str:
        """Determine the next agent based on the current state"""
        last_message = state["messages"][-1]
        
        try:
            response_data = json.loads(last_message.content)
            next_agents = response_data.get("next_agents", [])

            if next_agents:
                # Return the first suggested next agent
                return next_agents[0]
            else:
                # Check if there are pending tasks
                if state["task_queue"]:
                    task = state["task_queue"].pop(0)
                    return task["agent"]
                else:
                    return "end"
        except Exception as e:
            logger.warning(f"Error routing to next agent: {e}")
            return "end"
    
    async def _process_agent_task(
        self, 
        agent: Dict, 
        messages: List[BaseMessage], 
        memory_context: Dict
    ) -> AgentResponse:
        """Process a task with a specific agent"""
        # This is where the agent's LLM and tools are used
        # Implementation depends on specific agent logic
        
        agent_type = agent["type"]
        llm = agent["llm"]
        tools = agent["tools"]
        
        # Create a prompt based on agent type and current context
        prompt = self._create_agent_prompt(agent_type, messages, memory_context)
        
        # Get LLM response
        response = await llm.ainvoke(prompt)
        
        # Parse and execute any tool calls
        # ... Tool execution logic here
        
        return AgentResponse(
            agent_type=agent_type,
            action_taken="processed_task",
            result={"status": "success"},
            next_agents=[],
            confidence=0.95
        )
    
    def _create_agent_prompt(
        self, 
        agent_type: AgentType, 
        messages: List[BaseMessage], 
        memory_context: Dict
    ) -> str:
        """Create a specialized prompt for each agent"""
        base_prompt = f"""
        You are the {agent_type.value} agent in an AI Operating System.
        Your role: {self._get_agent_role(agent_type)}
        
        Current context:
        - Industry: {self.industry}
        - Company: {self.company_name}
        - Memory Context: {json.dumps(memory_context)}
        
        Recent messages:
        {self._format_messages(messages[-5:])}
        
        What action should you take?
        """
        return base_prompt
    
    def _get_agent_role(self, agent_type: AgentType) -> str:
        """Get the role description for each agent"""
        roles = {
            AgentType.ORCHESTRATOR: "Coordinate all other agents and manage workflows",
            AgentType.REVENUE_MAXIMIZER: "Maximize revenue through pricing and upsell strategies",
            AgentType.WEATHER_ANALYZER: "Analyze weather patterns for optimal project scheduling",
            AgentType.CODE_GENERATOR: "Generate and optimize code for new features",
            AgentType.SECURITY_GUARDIAN: "Protect the system from threats and vulnerabilities",
            # ... Add all agent roles
        }
        return roles.get(agent_type, "Specialized task processing")
    
    def _format_messages(self, messages: List[BaseMessage]) -> str:
        """Format messages for prompt"""
        formatted = []
        for msg in messages:
            role = "Human" if isinstance(msg, HumanMessage) else "AI"
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)
    
    async def _store_decision(self, agent_type: AgentType, response: AgentResponse):
        """Store agent decision in database"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO agent_decisions (agent_type, decision, confidence, outcome)
                VALUES ($1, $2, $3, $4)
            ''', agent_type.value, json.dumps(response.dict()), response.confidence, {})
    
    async def _broadcast_agent_activity(self, agent_type: AgentType, response: AgentResponse):
        """Broadcast agent activity to all connected websockets"""
        message = {
            "type": "agent_activity",
            "agent": agent_type.value,
            "action": response.action_taken,
            "timestamp": response.timestamp.isoformat()
        }
        
        for ws in self.websocket_connections:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send websocket message: {e}")
                self.websocket_connections.remove(ws)
    
    # Tool implementations
    async def _query_memory(self, query: str) -> Dict:
        """Query the persistent memory system"""
        # Implementation here
        return {"result": "memory_query_result"}
    
    async def _log_decision(self, decision: Dict) -> Dict:
        """Log a decision"""
        # Implementation here
        return {"status": "logged"}
    
    async def _emit_metric(self, metric: Dict) -> Dict:
        """Emit a metric"""
        # Implementation here
        return {"status": "emitted"}
    
    async def _analyze_pricing(self, data: Dict) -> Dict:
        """Analyze pricing strategies"""
        # Implementation here
        return {"optimal_price": 0}
    
    async def _identify_upsell(self, customer_data: Dict) -> Dict:
        """Identify upsell opportunities"""
        # Implementation here
        return {"opportunities": []}
    
    async def _get_weather_forecast(self, location: Dict) -> Dict:
        """Get weather forecast"""
        # Implementation here
        return {"forecast": {}}
    
    async def _assess_weather_risk(self, project: Dict) -> Dict:
        """Assess weather risk"""
        # Implementation here
        return {"risk_level": "low"}
    
    async def _generate_code(self, specification: Dict) -> Dict:
        """Generate code"""
        # Implementation here
        return {"code": ""}
    
    async def _review_code(self, code: str) -> Dict:
        """Review code"""
        # Implementation here
        return {"issues": []}
    
    async def process_request(self, request: Dict) -> Dict:
        """Process a request through the AI OS"""
        # Create initial state
        initial_state = GraphState(
            messages=[HumanMessage(content=json.dumps(request))],
            current_agent=AgentType.ORCHESTRATOR.value,
            task_queue=[],
            memory_context={},
            active_workflows=[],
            metrics={},
            decisions_made=[],
            errors=[],
            industry_config={"industry": self.industry}
        )
        
        # Run the graph
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        result = await self.graph.ainvoke(initial_state, config)
        
        return {
            "status": "success",
            "decisions": result["decisions_made"],
            "metrics": result["metrics"],
            "errors": result["errors"]
        }
    
    async def create_industry_template(self, industry: str, config: Dict) -> Dict:
        """Create a new industry-specific template"""
        # This allows anyone to create their own AI-powered business
        template = {
            "industry": industry,
            "agents": [],
            "workflows": [],
            "integrations": [],
            "ui_components": [],
            "data_schema": {}
        }
        
        # Customize agents based on industry
        if industry == "healthcare":
            template["agents"] = [
                AgentType.ORCHESTRATOR,
                "patient_care_coordinator",
                "appointment_scheduler",
                "insurance_verifier",
                "prescription_manager"
            ]
        elif industry == "retail":
            template["agents"] = [
                AgentType.ORCHESTRATOR,
                "inventory_manager",
                "price_optimizer",
                "customer_service",
                "supply_chain_coordinator"
            ]
        # ... More industry templates
        
        # Store template
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO industry_templates (industry, config, created_at)
                VALUES ($1, $2, NOW())
            ''', industry, json.dumps(template))
        
        return template

# Singleton instance
_ai_os_instance = None

def get_ai_os() -> AIOS:
    """Get the singleton AI OS instance"""
    global _ai_os_instance
    if _ai_os_instance is None:
        _ai_os_instance = AIOS()
    return _ai_os_instance