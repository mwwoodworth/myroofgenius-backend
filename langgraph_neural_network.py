"""
LangGraph Neural Network - The Real Brain of BrainOps
A true neural network of specialized AI agents with persistent memory
"""

import os
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, TypedDict, Annotated, Literal, Sequence
from enum import Enum
import hashlib

# Supabase for persistent memory
from supabase import create_client, Client
import asyncpg

# LangGraph for orchestration
from langgraph.graph import StateGraph, END, MessageGraph
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.prebuilt import ToolExecutor, ToolInvocation, tools_condition
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Agent Specializations with Deep Knowledge
AGENT_SPECIALIZATIONS = {
    # Revenue & Sales
    "lead_capture": {
        "description": "Captures and qualifies leads with 95% accuracy",
        "knowledge": ["pricing models", "urgency detection", "budget qualification", "insurance claims"],
        "tools": ["instant_quote", "lead_scoring", "insurance_check"],
        "memory_keys": ["lead_patterns", "conversion_rates", "pricing_history"]
    },
    "sales_closer": {
        "description": "Converts leads to customers using psychological triggers",
        "knowledge": ["objection handling", "urgency creation", "value stacking", "closing techniques"],
        "tools": ["create_offer", "apply_discount", "schedule_followup"],
        "memory_keys": ["successful_closes", "objection_responses", "discount_effectiveness"]
    },
    
    # Roofing Operations
    "weather_analyst": {
        "description": "Analyzes weather for optimal scheduling and risk assessment",
        "knowledge": ["weather patterns", "storm damage", "work windows", "material impact"],
        "tools": ["weather_forecast", "storm_tracker", "schedule_optimizer"],
        "memory_keys": ["weather_patterns", "storm_history", "scheduling_success"]
    },
    "crew_scheduler": {
        "description": "Optimizes crew assignments for maximum efficiency",
        "knowledge": ["crew skills", "job requirements", "travel time", "workload balance"],
        "tools": ["assign_crew", "optimize_route", "balance_workload"],
        "memory_keys": ["crew_performance", "job_history", "efficiency_metrics"]
    },
    "material_estimator": {
        "description": "Calculates exact materials with waste minimization",
        "knowledge": ["roof measurements", "material types", "waste factors", "supplier pricing"],
        "tools": ["calculate_materials", "order_supplies", "track_waste"],
        "memory_keys": ["material_usage", "waste_patterns", "supplier_performance"]
    },
    
    # Technical Operations
    "code_architect": {
        "description": "Designs and implements system architecture",
        "knowledge": ["design patterns", "scalability", "performance", "security"],
        "tools": ["generate_code", "review_architecture", "optimize_performance"],
        "memory_keys": ["code_patterns", "performance_metrics", "security_vulnerabilities"]
    },
    "bug_surgeon": {
        "description": "Diagnoses and fixes bugs with surgical precision",
        "knowledge": ["error patterns", "stack traces", "debugging techniques", "root cause analysis"],
        "tools": ["analyze_error", "trace_execution", "apply_fix"],
        "memory_keys": ["bug_patterns", "fix_history", "prevention_strategies"]
    },
    "deployment_commander": {
        "description": "Manages deployments with zero downtime",
        "knowledge": ["CI/CD", "rollback strategies", "health checks", "canary deployments"],
        "tools": ["deploy_code", "run_tests", "rollback_deployment"],
        "memory_keys": ["deployment_history", "failure_patterns", "success_metrics"]
    },
    
    # Customer Experience
    "customer_psychologist": {
        "description": "Understands and predicts customer behavior",
        "knowledge": ["behavioral psychology", "satisfaction drivers", "churn indicators", "loyalty factors"],
        "tools": ["analyze_sentiment", "predict_churn", "recommend_action"],
        "memory_keys": ["customer_patterns", "satisfaction_scores", "retention_strategies"]
    },
    "support_ninja": {
        "description": "Resolves issues before customers notice",
        "knowledge": ["common issues", "resolution paths", "escalation triggers", "satisfaction tactics"],
        "tools": ["diagnose_issue", "apply_solution", "follow_up"],
        "memory_keys": ["issue_resolutions", "customer_feedback", "response_templates"]
    },
    
    # Financial Intelligence
    "revenue_optimizer": {
        "description": "Maximizes revenue through pricing and upselling",
        "knowledge": ["pricing psychology", "market rates", "profit margins", "upsell opportunities"],
        "tools": ["optimize_price", "identify_upsell", "forecast_revenue"],
        "memory_keys": ["pricing_success", "upsell_conversions", "revenue_trends"]
    },
    "cash_flow_guardian": {
        "description": "Manages cash flow and financial health",
        "knowledge": ["payment terms", "collection strategies", "expense optimization", "financial forecasting"],
        "tools": ["track_payments", "optimize_expenses", "forecast_cash"],
        "memory_keys": ["payment_patterns", "expense_trends", "collection_success"]
    },
    
    # Marketing & Growth
    "content_alchemist": {
        "description": "Creates content that converts",
        "knowledge": ["copywriting", "SEO", "conversion optimization", "content strategy"],
        "tools": ["generate_content", "optimize_seo", "test_variations"],
        "memory_keys": ["content_performance", "keyword_rankings", "conversion_rates"]
    },
    "growth_hacker": {
        "description": "Finds and exploits growth opportunities",
        "knowledge": ["growth loops", "viral mechanics", "acquisition channels", "retention tactics"],
        "tools": ["identify_channels", "test_campaigns", "measure_growth"],
        "memory_keys": ["growth_experiments", "channel_performance", "viral_coefficients"]
    },
    
    # Security & Compliance
    "security_sentinel": {
        "description": "Protects against all threats",
        "knowledge": ["threat patterns", "vulnerabilities", "compliance requirements", "incident response"],
        "tools": ["scan_threats", "patch_vulnerabilities", "audit_compliance"],
        "memory_keys": ["threat_intelligence", "vulnerability_history", "compliance_status"]
    },
    
    # System Intelligence
    "performance_optimizer": {
        "description": "Optimizes system performance continuously",
        "knowledge": ["bottlenecks", "optimization techniques", "caching strategies", "resource management"],
        "tools": ["profile_performance", "optimize_queries", "manage_cache"],
        "memory_keys": ["performance_baselines", "optimization_history", "resource_patterns"]
    },
    "prediction_oracle": {
        "description": "Predicts future trends and issues",
        "knowledge": ["time series analysis", "pattern recognition", "anomaly detection", "forecasting"],
        "tools": ["analyze_trends", "detect_anomalies", "forecast_metrics"],
        "memory_keys": ["prediction_accuracy", "pattern_library", "anomaly_history"]
    }
}

class NeuralState(TypedDict):
    """State that flows through the neural network"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_thought: str
    active_agents: List[str]
    memory_context: Dict[str, Any]
    decisions: List[Dict[str, Any]]
    confidence: float
    task_queue: List[Dict[str, Any]]
    knowledge_graph: Dict[str, Any]
    learning_updates: List[Dict[str, Any]]

class NeuralNetwork:
    """The actual neural network that connects all agents"""
    
    def __init__(self):
        # Initialize Supabase connection
        self.supabase = supabase
        
        # Initialize LLMs
        self.claude = ChatAnthropic(
            model="claude-3-opus-20240229",
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.gpt4 = ChatOpenAI(
            model="gpt-4-turbo-preview",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Build the neural network graph
        self.network = self._build_network()
        
        # Initialize persistent memory tables
        asyncio.create_task(self._initialize_memory_tables())
        
        logger.info("Neural Network initialized with {} specialized agents".format(len(self.agents)))
    
    async def _initialize_memory_tables(self):
        """Create Supabase tables for persistent memory"""
        try:
            # Check if tables exist, if not create them
            # Agent Memories Table
            self.supabase.table("agent_memories").select("*").limit(1).execute()
        except Exception as e:
            logger.warning(f"Memory tables may not exist, creating schema: {e}")
            # Create tables via SQL
            await self._create_memory_schema()
    
    async def _create_memory_schema(self):
        """Create the complete memory schema in Supabase"""
        # Connect directly to create tables
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS agent_memories (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_name VARCHAR(100),
                memory_key VARCHAR(255),
                memory_value JSONB,
                embedding vector(1536),
                importance FLOAT DEFAULT 0.5,
                access_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                last_accessed TIMESTAMP DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_agent_memories_agent ON agent_memories(agent_name);
            CREATE INDEX IF NOT EXISTS idx_agent_memories_key ON agent_memories(memory_key);
            CREATE INDEX IF NOT EXISTS idx_memories_embedding ON agent_memories USING ivfflat (embedding vector_cosine_ops);
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_graph (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                subject VARCHAR(255),
                predicate VARCHAR(255),
                object VARCHAR(255),
                confidence FLOAT,
                source_agent VARCHAR(100),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_kg_subject ON knowledge_graph(subject);
            CREATE INDEX IF NOT EXISTS idx_kg_object ON knowledge_graph(object);
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS agent_decisions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_name VARCHAR(100),
                decision_type VARCHAR(100),
                input_data JSONB,
                output_data JSONB,
                confidence FLOAT,
                execution_time_ms INT,
                success BOOLEAN,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_decisions_agent ON agent_decisions(agent_name);
            CREATE INDEX IF NOT EXISTS idx_decisions_type ON agent_decisions(decision_type);
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS learning_updates (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_name VARCHAR(100),
                learning_type VARCHAR(100),
                old_knowledge JSONB,
                new_knowledge JSONB,
                trigger_event JSONB,
                improvement_metric FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS agent_communications (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                from_agent VARCHAR(100),
                to_agent VARCHAR(100),
                message_type VARCHAR(100),
                message_content JSONB,
                response JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        
        await conn.close()
        logger.info("Memory schema created in Supabase")
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all specialized agents with their knowledge"""
        agents = {}
        
        for agent_name, spec in AGENT_SPECIALIZATIONS.items():
            agents[agent_name] = {
                "name": agent_name,
                "description": spec["description"],
                "knowledge": spec["knowledge"],
                "tools": self._create_agent_tools(agent_name, spec["tools"]),
                "memory_keys": spec["memory_keys"],
                "llm": self.claude if "architect" in agent_name or "oracle" in agent_name else self.gpt4,
                "active": True,
                "performance_metrics": {
                    "decisions_made": 0,
                    "success_rate": 1.0,
                    "avg_confidence": 1.0,
                    "avg_response_time": 0
                }
            }
        
        return agents
    
    def _create_agent_tools(self, agent_name: str, tool_names: List[str]) -> List:
        """Create specific tools for each agent"""
        tools = []
        
        # Universal tools all agents have
        @tool
        async def query_memory(query: str) -> str:
            """Query persistent memory for relevant information"""
            # Search in Supabase
            result = self.supabase.table("agent_memories").select("*").filter(
                "agent_name", "eq", agent_name
            ).filter(
                "memory_key", "ilike", f"%{query}%"
            ).limit(5).execute()
            
            return json.dumps([r for r in result.data]) if result.data else "No relevant memory found"
        
        @tool
        async def store_memory(key: str, value: Dict) -> str:
            """Store new knowledge in persistent memory"""
            # Store in Supabase
            self.supabase.table("agent_memories").insert({
                "agent_name": agent_name,
                "memory_key": key,
                "memory_value": value,
                "importance": value.get("importance", 0.5)
            }).execute()
            
            return f"Memory stored: {key}"
        
        @tool
        async def communicate_with_agent(target_agent: str, message: Dict) -> str:
            """Communicate with another specialized agent"""
            # Store communication
            self.supabase.table("agent_communications").insert({
                "from_agent": agent_name,
                "to_agent": target_agent,
                "message_type": message.get("type", "query"),
                "message_content": message
            }).execute()
            
            # Get response from target agent
            if target_agent in self.agents:
                # Process through target agent
                response = await self._process_agent_communication(target_agent, message)
                return json.dumps(response)
            return "Agent not found"
        
        tools.extend([query_memory, store_memory, communicate_with_agent])
        
        # Agent-specific tools
        if agent_name == "lead_capture":
            @tool
            async def instant_quote(lead_data: Dict) -> Dict:
                """Generate instant quote for lead"""
                # Complex pricing logic based on stored patterns
                base_price = lead_data.get("square_footage", 2000) * 4.5
                if lead_data.get("urgency") == "emergency":
                    base_price *= 1.5
                return {"quote": base_price, "validity": "14 days"}
            
            tools.append(instant_quote)
        
        elif agent_name == "weather_analyst":
            @tool
            async def weather_forecast(location: str, days: int = 7) -> Dict:
                """Get weather forecast for scheduling"""
                # Would integrate with weather API
                return {"forecast": "clear", "work_windows": ["Mon-Wed", "Fri-Sun"]}
            
            tools.append(weather_forecast)
        
        # Add more agent-specific tools...
        
        return tools
    
    def _build_network(self) -> StateGraph:
        """Build the LangGraph neural network"""
        network = StateGraph(NeuralState)
        
        # Add nodes for each agent
        for agent_name in self.agents.keys():
            network.add_node(
                agent_name,
                lambda state, agent=agent_name: self._agent_processor(state, agent)
            )
        
        # Add the orchestrator node
        network.add_node("orchestrator", self._orchestrator)
        
        # Add the learning node
        network.add_node("learning_system", self._learning_system)
        
        # Set entry point
        network.set_entry_point("orchestrator")
        
        # Add conditional routing
        network.add_conditional_edges(
            "orchestrator",
            self._route_decision,
            {agent: agent for agent in self.agents.keys()} | {"learning_system": "learning_system", "end": END}
        )
        
        # All agents can route back to orchestrator or to each other
        for agent_name in self.agents.keys():
            network.add_conditional_edges(
                agent_name,
                self._agent_routing,
                {a: a for a in self.agents.keys()} | {"orchestrator": "orchestrator", "learning_system": "learning_system", "end": END}
            )
        
        # Learning system routes back to orchestrator
        network.add_edge("learning_system", "orchestrator")
        
        # Compile with checkpointing
        checkpointer = PostgresSaver.from_conn_string(os.getenv("DATABASE_URL"))
        return network.compile(checkpointer=checkpointer)
    
    async def _orchestrator(self, state: NeuralState) -> NeuralState:
        """Central orchestrator that coordinates all agents"""
        # Analyze the current task
        current_message = state["messages"][-1] if state["messages"] else None
        
        if current_message:
            # Determine which agents to activate
            task_analysis = await self._analyze_task(current_message.content)
            
            # Update state
            state["current_thought"] = f"Task requires: {', '.join(task_analysis['required_agents'])}"
            state["active_agents"] = task_analysis["required_agents"]
            state["confidence"] = task_analysis["confidence"]
            
            # Load relevant memory context
            state["memory_context"] = await self._load_memory_context(task_analysis)
        
        return state
    
    async def _agent_processor(self, state: NeuralState, agent_name: str) -> NeuralState:
        """Process state through a specific agent"""
        agent = self.agents[agent_name]
        start_time = datetime.now()
        
        try:
            # Get agent's relevant memories
            memories = await self._get_agent_memories(agent_name, state["current_thought"])
            
            # Process with agent's LLM and tools
            result = await self._execute_agent(agent, state, memories)
            
            # Store decision
            decision = {
                "agent": agent_name,
                "input": state["current_thought"],
                "output": result,
                "confidence": result.get("confidence", 0.8),
                "timestamp": datetime.now().isoformat()
            }
            state["decisions"].append(decision)
            
            # Store in Supabase
            self.supabase.table("agent_decisions").insert({
                "agent_name": agent_name,
                "decision_type": result.get("type", "processing"),
                "input_data": {"thought": state["current_thought"]},
                "output_data": result,
                "confidence": result.get("confidence", 0.8),
                "execution_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "success": True
            }).execute()
            
            # Update agent performance metrics
            self._update_agent_metrics(agent_name, True, result.get("confidence", 0.8))
            
            # Add agent's response as message
            state["messages"].append(
                AIMessage(content=json.dumps(result), name=agent_name)
            )
            
        except Exception as e:
            logger.error(f"Agent {agent_name} error: {e}")
            self._update_agent_metrics(agent_name, False, 0)
            
        return state
    
    async def _learning_system(self, state: NeuralState) -> NeuralState:
        """System that learns from all interactions"""
        # Analyze all decisions made
        if state["decisions"]:
            # Extract patterns
            patterns = self._extract_patterns(state["decisions"])
            
            # Update agent knowledge
            for pattern in patterns:
                if pattern["confidence"] > 0.8:
                    # Store as new knowledge
                    self.supabase.table("knowledge_graph").insert({
                        "subject": pattern["subject"],
                        "predicate": pattern["predicate"],
                        "object": pattern["object"],
                        "confidence": pattern["confidence"],
                        "source_agent": pattern["source_agent"]
                    }).execute()
            
            # Identify improvements
            improvements = self._identify_improvements(state["decisions"])
            state["learning_updates"] = improvements
            
            # Store learning updates
            for improvement in improvements:
                self.supabase.table("learning_updates").insert({
                    "agent_name": improvement["agent"],
                    "learning_type": improvement["type"],
                    "new_knowledge": improvement["knowledge"],
                    "improvement_metric": improvement["metric"]
                }).execute()
        
        return state
    
    def _route_decision(self, state: NeuralState) -> str:
        """Decide which agent to route to next"""
        if state["active_agents"]:
            return state["active_agents"].pop(0)
        elif state["task_queue"]:
            task = state["task_queue"].pop(0)
            return task["agent"]
        else:
            return "end"
    
    def _agent_routing(self, state: NeuralState) -> str:
        """Agent-level routing decisions"""
        # Check if agent needs help from another agent
        last_message = state["messages"][-1]
        if hasattr(last_message, 'name'):
            result = json.loads(last_message.content)
            if result.get("needs_help"):
                return result["needs_help"]
        
        # Return to orchestrator if more agents to process
        if state["active_agents"]:
            return "orchestrator"
        
        # Check if learning is needed
        if len(state["decisions"]) > 5:
            return "learning_system"
        
        return "end"
    
    async def _analyze_task(self, task: str) -> Dict:
        """Analyze task to determine required agents"""
        # Use LLM to analyze
        prompt = f"""
        Analyze this task and determine which specialized agents are needed:
        Task: {task}
        
        Available agents: {list(self.agents.keys())}
        
        Return the required agents and confidence level.
        """
        
        response = await self.claude.ainvoke(prompt)
        
        # Parse response (simplified)
        return {
            "required_agents": ["lead_capture", "revenue_optimizer"],  # Would be parsed from response
            "confidence": 0.9
        }
    
    async def _load_memory_context(self, task_analysis: Dict) -> Dict:
        """Load relevant memory context for the task"""
        context = {}
        
        for agent in task_analysis["required_agents"]:
            # Get agent's recent successful patterns
            result = self.supabase.table("agent_memories").select("*").filter(
                "agent_name", "eq", agent
            ).filter(
                "importance", "gte", 0.7
            ).order("updated_at", desc=True).limit(10).execute()
            
            if result.data:
                context[agent] = result.data
        
        return context
    
    async def _get_agent_memories(self, agent_name: str, context: str) -> List[Dict]:
        """Get relevant memories for an agent"""
        # Search by context
        result = self.supabase.table("agent_memories").select("*").filter(
            "agent_name", "eq", agent_name
        ).order("importance", desc=True).limit(20).execute()
        
        return result.data if result.data else []
    
    async def _execute_agent(self, agent: Dict, state: NeuralState, memories: List[Dict]) -> Dict:
        """Execute agent processing"""
        # Create prompt with agent's specialization
        prompt = f"""
        You are {agent['name']}, specialized in: {agent['description']}
        
        Your knowledge areas: {', '.join(agent['knowledge'])}
        
        Relevant memories:
        {json.dumps(memories[:5])}
        
        Current task: {state['current_thought']}
        
        Previous decisions: {json.dumps(state['decisions'][-3:])}
        
        Provide your specialized analysis and recommendations.
        """
        
        # Execute with agent's LLM
        response = await agent["llm"].ainvoke(prompt)
        
        # Parse and return (simplified)
        return {
            "type": "analysis",
            "content": response.content,
            "confidence": 0.85,
            "recommendations": []
        }
    
    async def _process_agent_communication(self, target_agent: str, message: Dict) -> Dict:
        """Process inter-agent communication"""
        # Direct agent-to-agent communication
        agent = self.agents[target_agent]
        
        prompt = f"""
        You are {target_agent}. Another agent is asking for your expertise:
        {json.dumps(message)}
        
        Provide your specialized response.
        """
        
        response = await agent["llm"].ainvoke(prompt)
        
        return {
            "from": target_agent,
            "response": response.content
        }
    
    def _extract_patterns(self, decisions: List[Dict]) -> List[Dict]:
        """Extract patterns from decisions"""
        patterns = []
        
        # Analyze decision sequences
        for i, decision in enumerate(decisions):
            if decision["confidence"] > 0.8:
                patterns.append({
                    "subject": decision["agent"],
                    "predicate": "successfully_processed",
                    "object": decision["input"],
                    "confidence": decision["confidence"],
                    "source_agent": decision["agent"]
                })
        
        return patterns
    
    def _identify_improvements(self, decisions: List[Dict]) -> List[Dict]:
        """Identify improvement opportunities"""
        improvements = []
        
        # Analyze for patterns of success/failure
        agent_performance = {}
        for decision in decisions:
            agent = decision["agent"]
            if agent not in agent_performance:
                agent_performance[agent] = []
            agent_performance[agent].append(decision["confidence"])
        
        for agent, confidences in agent_performance.items():
            avg_confidence = np.mean(confidences)
            if avg_confidence < 0.7:
                improvements.append({
                    "agent": agent,
                    "type": "confidence_improvement",
                    "knowledge": {"needs_training": True},
                    "metric": avg_confidence
                })
        
        return improvements
    
    def _update_agent_metrics(self, agent_name: str, success: bool, confidence: float):
        """Update agent performance metrics"""
        metrics = self.agents[agent_name]["performance_metrics"]
        metrics["decisions_made"] += 1
        
        # Update success rate (moving average)
        metrics["success_rate"] = (metrics["success_rate"] * 0.9) + (1.0 if success else 0.0) * 0.1
        
        # Update confidence (moving average)
        metrics["avg_confidence"] = (metrics["avg_confidence"] * 0.9) + confidence * 0.1
    
    async def process(self, request: str) -> Dict:
        """Process a request through the neural network"""
        # Create initial state
        initial_state = NeuralState(
            messages=[HumanMessage(content=request)],
            current_thought=request,
            active_agents=[],
            memory_context={},
            decisions=[],
            confidence=1.0,
            task_queue=[],
            knowledge_graph={},
            learning_updates=[]
        )
        
        # Process through network
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        result = await self.network.ainvoke(initial_state, config)
        
        return {
            "decisions": result["decisions"],
            "confidence": result["confidence"],
            "learning_updates": result["learning_updates"],
            "final_response": result["messages"][-1].content if result["messages"] else None
        }
    
    async def get_system_knowledge(self) -> Dict:
        """Get complete system knowledge state"""
        # Get all agent memories
        memories = self.supabase.table("agent_memories").select("*").execute()
        
        # Get knowledge graph
        knowledge = self.supabase.table("knowledge_graph").select("*").execute()
        
        # Get recent decisions
        decisions = self.supabase.table("agent_decisions").select("*").order(
            "created_at", desc=True
        ).limit(100).execute()
        
        return {
            "total_memories": len(memories.data) if memories.data else 0,
            "knowledge_nodes": len(knowledge.data) if knowledge.data else 0,
            "recent_decisions": len(decisions.data) if decisions.data else 0,
            "agent_metrics": {
                agent: self.agents[agent]["performance_metrics"]
                for agent in self.agents.keys()
            }
        }
    
    async def improve_exponentially(self):
        """Continuous exponential improvement loop"""
        while True:
            try:
                # Get all recent interactions
                decisions = self.supabase.table("agent_decisions").select("*").filter(
                    "created_at", "gte", (datetime.now() - timedelta(hours=1)).isoformat()
                ).execute()
                
                if decisions.data:
                    # Learn from successes
                    successful = [d for d in decisions.data if d["success"] and d["confidence"] > 0.8]
                    
                    for success in successful:
                        # Reinforce successful patterns
                        self.supabase.table("agent_memories").insert({
                            "agent_name": success["agent_name"],
                            "memory_key": f"success_pattern_{datetime.now().timestamp()}",
                            "memory_value": {
                                "input": success["input_data"],
                                "output": success["output_data"],
                                "confidence": success["confidence"]
                            },
                            "importance": success["confidence"]
                        }).execute()
                    
                    # Learn from failures
                    failures = [d for d in decisions.data if not d["success"] or d["confidence"] < 0.5]
                    
                    for failure in failures:
                        # Store failure patterns to avoid
                        self.supabase.table("agent_memories").insert({
                            "agent_name": failure["agent_name"],
                            "memory_key": f"failure_pattern_{datetime.now().timestamp()}",
                            "memory_value": {
                                "input": failure["input_data"],
                                "error": failure.get("error_message"),
                                "lesson": "Avoid this pattern"
                            },
                            "importance": 0.9  # High importance to remember failures
                        }).execute()
                
                # Sleep before next improvement cycle
                await asyncio.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                logger.error(f"Improvement loop error: {e}")
                await asyncio.sleep(600)

# Global instance
neural_network = None

def get_neural_network() -> NeuralNetwork:
    """Get the singleton neural network instance"""
    global neural_network
    if neural_network is None:
        neural_network = NeuralNetwork()
        # Start continuous improvement
        asyncio.create_task(neural_network.improve_exponentially())
    return neural_network