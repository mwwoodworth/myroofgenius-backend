#!/usr/bin/env python3
"""
BrainOps AI Board - LangGraph Orchestration
Version: 1.0.0
Multi-agent orchestration with persistent memory
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
from uuid import uuid4
import psycopg2
from psycopg2.extras import RealDictCursor

from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
import httpx

# Database configuration
DB_CONFIG = {
    'host': 'aws-0-us-east-2.pooler.supabase.com',
    'port': 6543,
    'database': 'postgres',
    'user': 'postgres.yomagoqdmxszqtdwuhab',
    'password': '<DB_PASSWORD_REDACTED>'
}

# Agent configurations
AGENTS = {
    "strategic": {
        "name": "Gemini Strategic",
        "model": "gemini-pro",
        "role": "Strategic planning and high-level decisions",
        "provider": "google"
    },
    "operational": {
        "name": "ChatGPT Operational",
        "model": "gpt-4-turbo-preview",
        "role": "Operational execution and task management",
        "provider": "openai"
    },
    "content": {
        "name": "Claude Content",
        "model": "claude-3-opus-20240229",
        "role": "Content creation and documentation",
        "provider": "anthropic"
    },
    "research": {
        "name": "Perplexity Research",
        "model": "pplx-70b-online",
        "role": "Research and information gathering",
        "provider": "perplexity"
    },
    "knowledge": {
        "name": "Notebook LM Knowledge",
        "model": "notebook-lm",
        "role": "Knowledge synthesis and insights",
        "provider": "google"
    }
}

# State definition
class AgentState(TypedDict):
    messages: List[Dict]
    current_agent: str
    task_id: str
    epic_id: str
    decision_log: List[Dict]
    memory_refs: List[str]
    artifacts: List[Dict]
    error: Optional[str]
    final_output: Optional[Dict]

class AIBoard:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.agents = self._initialize_agents()
        self.graph = self._build_graph()
        self.memory = MemorySaver()
        
    def _initialize_agents(self) -> Dict:
        """Initialize all AI agents"""
        agents = {}
        
        # Strategic Agent (Gemini)
        if os.getenv('GOOGLE_API_KEY'):
            agents['strategic'] = ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=os.getenv('GOOGLE_API_KEY')
            )
        
        # Operational Agent (ChatGPT)
        if os.getenv('OPENAI_API_KEY'):
            agents['operational'] = ChatOpenAI(
                model="gpt-4-turbo-preview",
                openai_api_key=os.getenv('OPENAI_API_KEY')
            )
        
        # Content Agent (Claude)
        if os.getenv('ANTHROPIC_API_KEY'):
            agents['content'] = ChatAnthropic(
                model="claude-3-opus-20240229",
                anthropic_api_key=os.getenv('ANTHROPIC_API_KEY')
            )
        
        # For now, use placeholders for Perplexity and Notebook LM
        agents['research'] = agents.get('operational', None)
        agents['knowledge'] = agents.get('strategic', None)
        
        return agents
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph orchestration"""
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("strategic", self.strategic_node)
        workflow.add_node("operational", self.operational_node)
        workflow.add_node("content", self.content_node)
        workflow.add_node("research", self.research_node)
        workflow.add_node("knowledge", self.knowledge_node)
        workflow.add_node("aurea", self.aurea_conductor)
        workflow.add_node("memory_bus", self.memory_bus)
        workflow.add_node("decision_logger", self.decision_logger)
        
        # Define edges
        workflow.add_edge("aurea", "strategic")
        workflow.add_edge("strategic", "operational")
        workflow.add_edge("operational", "content")
        workflow.add_edge("content", "research")
        workflow.add_edge("research", "knowledge")
        workflow.add_edge("knowledge", "memory_bus")
        workflow.add_edge("memory_bus", "decision_logger")
        workflow.add_edge("decision_logger", END)
        
        # Set entry point
        workflow.set_entry_point("aurea")
        
        return workflow.compile(checkpointer=self.memory)
    
    async def strategic_node(self, state: AgentState) -> AgentState:
        """Strategic planning node"""
        if 'strategic' not in self.agents:
            state['error'] = "Strategic agent not configured"
            return state
        
        messages = state['messages']
        response = await self.agents['strategic'].ainvoke(messages)
        
        state['messages'].append({
            "role": "strategic",
            "content": response.content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Store in memory
        self._store_memory("strategic", "gemini", response.content, state['task_id'])
        
        return state
    
    async def operational_node(self, state: AgentState) -> AgentState:
        """Operational execution node"""
        if 'operational' not in self.agents:
            state['error'] = "Operational agent not configured"
            return state
        
        messages = state['messages']
        response = await self.agents['operational'].ainvoke(messages)
        
        state['messages'].append({
            "role": "operational",
            "content": response.content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Create tasks in Task OS
        self._create_operational_tasks(response.content, state['epic_id'])
        
        return state
    
    async def content_node(self, state: AgentState) -> AgentState:
        """Content creation node"""
        if 'content' not in self.agents:
            state['error'] = "Content agent not configured"
            return state
        
        messages = state['messages']
        response = await self.agents['content'].ainvoke(messages)
        
        state['messages'].append({
            "role": "content",
            "content": response.content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Store documentation
        self._store_documentation(response.content, state['task_id'])
        
        return state
    
    async def research_node(self, state: AgentState) -> AgentState:
        """Research node"""
        # Implement research logic
        state['messages'].append({
            "role": "research",
            "content": "Research completed",
            "timestamp": datetime.utcnow().isoformat()
        })
        return state
    
    async def knowledge_node(self, state: AgentState) -> AgentState:
        """Knowledge synthesis node"""
        # Implement knowledge synthesis
        state['messages'].append({
            "role": "knowledge",
            "content": "Knowledge synthesized",
            "timestamp": datetime.utcnow().isoformat()
        })
        return state
    
    async def aurea_conductor(self, state: AgentState) -> AgentState:
        """AUREA orchestration conductor"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Load context from database
        cursor.execute("""
            SELECT * FROM task_os.epics WHERE status = 'pending' 
            ORDER BY priority DESC LIMIT 1
        """)
        epic = cursor.fetchone()
        
        if epic:
            state['epic_id'] = str(epic['id'])
            state['task_id'] = str(uuid4())
            state['messages'] = [{
                "role": "system",
                "content": f"Working on epic: {epic['title']}\nDescription: {epic['description']}"
            }]
        
        cursor.close()
        return state
    
    async def memory_bus(self, state: AgentState) -> AgentState:
        """Memory persistence bus"""
        cursor = self.conn.cursor()
        
        for msg in state['messages']:
            cursor.execute("""
                INSERT INTO memory.agent_memories 
                (agent_id, agent_type, scope, memory_type, content, content_hash, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                msg.get('role', 'unknown'),
                'aurea',
                'project',
                'procedure',
                msg['content'],
                hashlib.sha256(msg['content'].encode()).hexdigest(),
                ['ai_board', state.get('epic_id', '')]
            ))
        
        self.conn.commit()
        cursor.close()
        return state
    
    async def decision_logger(self, state: AgentState) -> AgentState:
        """Log all decisions to database"""
        cursor = self.conn.cursor()
        
        decision_id = str(uuid4())
        cursor.execute("""
            INSERT INTO ops.decisions 
            (decision_id, who, what, why, decision_type, options, selected, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            decision_id,
            'AI Board',
            f"Executed task for epic {state.get('epic_id', 'unknown')}",
            "Automated orchestration based on priority",
            'operational',
            json.dumps(state.get('decision_log', [])),
            json.dumps(state.get('final_output', {})),
            'AUREA'
        ))
        
        self.conn.commit()
        cursor.close()
        
        # Send to Slack
        self._notify_slack(state)
        
        return state
    
    def _store_memory(self, agent_id: str, agent_type: str, content: str, task_id: str):
        """Store agent memory"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO memory.agent_memories 
            (agent_id, agent_type, scope, memory_type, content, content_hash, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            agent_id,
            agent_type,
            'project',
            'insight',
            content,
            hashlib.sha256(content.encode()).hexdigest(),
            [task_id, 'ai_board']
        ))
        self.conn.commit()
        cursor.close()
    
    def _create_operational_tasks(self, content: str, epic_id: str):
        """Create tasks in Task OS"""
        cursor = self.conn.cursor()
        
        # Parse content for actionable items
        task_id = str(uuid4())
        cursor.execute("""
            INSERT INTO task_os.tasks 
            (id, title, description, epic_id, priority, assignee_agent, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            task_id,
            "AI Board Generated Task",
            content[:500],
            epic_id,
            3,
            'AUREA',
            'pending'
        ))
        self.conn.commit()
        cursor.close()
    
    def _store_documentation(self, content: str, task_id: str):
        """Store documentation in SOPs"""
        cursor = self.conn.cursor()
        sop_id = f"ai_board_{task_id}"
        
        cursor.execute("""
            INSERT INTO docs.sops 
            (sop_id, title, category, area, md_body, owner, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            sop_id,
            "AI Board Generated Documentation",
            'operational',
            'ai_board',
            content,
            'AI Board',
            'Claude'
        ))
        self.conn.commit()
        cursor.close()
    
    def _notify_slack(self, state: AgentState):
        """Send notification to Slack"""
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            return
        
        message = {
            "text": f"AI Board completed task {state.get('task_id', 'unknown')}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Epic:* {state.get('epic_id', 'unknown')}\n*Status:* Completed"
                    }
                }
            ]
        }
        
        try:
            httpx.post(webhook_url, json=message)
        except:
            pass
    
    async def run(self, input_data: Dict) -> Dict:
        """Run the AI Board orchestration"""
        initial_state = AgentState(
            messages=[],
            current_agent="aurea",
            task_id=str(uuid4()),
            epic_id="",
            decision_log=[],
            memory_refs=[],
            artifacts=[],
            error=None,
            final_output=None
        )
        
        # Merge input data
        initial_state.update(input_data)
        
        # Run the graph
        config = {"configurable": {"thread_id": initial_state['task_id']}}
        result = await self.graph.ainvoke(initial_state, config)
        
        return result

# CLI interface
async def main():
    board = AIBoard()
    
    # Run a test orchestration
    result = await board.run({
        "messages": [{
            "role": "user",
            "content": "Execute next priority epic from Task OS"
        }]
    })
    
    print(f"AI Board execution completed: {result.get('task_id')}")

if __name__ == "__main__":
    asyncio.run(main())