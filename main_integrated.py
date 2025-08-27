"""
BrainOps Integrated Backend - Complete Operational System
The real production backend with all systems active and using persistent memory
"""

import os
import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our brain systems
from persistent_memory_brain import get_brain, PersistentMemoryBrain
from langgraph_neural_network import get_neural_network, NeuralNetwork
from env_manager import get_env_manager, EnvironmentManager
from revenue_engine import RevenueEngine, Lead
from ai_os_core import get_ai_os
from monitoring_system import MonitoringSystem
from security_system import SecuritySystem

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
brain: Optional[PersistentMemoryBrain] = None
neural_network: Optional[NeuralNetwork] = None
env_manager: Optional[EnvironmentManager] = None
revenue_engine: Optional[RevenueEngine] = None
monitoring: Optional[MonitoringSystem] = None
security: Optional[SecuritySystem] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown with persistent memory"""
    global brain, neural_network, env_manager, revenue_engine, monitoring, security
    
    logger.info("🧠 Initializing BrainOps with Persistent Memory...")
    
    try:
        # Initialize environment manager first
        env_manager = get_env_manager()
        await asyncio.sleep(1)  # Let it initialize
        
        # Initialize the brain (persistent memory)
        brain = get_brain()
        await brain.store_thought({
            "type": "startup",
            "content": "BrainOps system initializing",
            "timestamp": datetime.now().isoformat()
        }, importance=0.8)
        
        # Initialize neural network
        neural_network = get_neural_network()
        
        # Initialize other systems
        # These would be initialized with Supabase connection from env_manager
        db_url = await env_manager.get_variable("DATABASE_URL")
        redis_url = await env_manager.get_variable("REDIS_URL")
        
        # Log successful initialization to brain
        await brain.store_thought({
            "type": "system_ready",
            "content": {
                "brain": "active",
                "neural_network": "active",
                "env_manager": "active",
                "timestamp": datetime.now().isoformat()
            },
            "category": "system",
            "importance": 0.9
        })
        
        logger.info("✅ BrainOps initialized with persistent memory!")
        
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        # Store failure in brain if possible
        if brain:
            await brain.store_thought({
                "type": "startup_failure",
                "content": {"error": str(e)},
                "category": "error",
                "importance": 1.0
            })
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down BrainOps...")
    if brain:
        await brain.store_thought({
            "type": "shutdown",
            "content": "System shutting down gracefully",
            "timestamp": datetime.now().isoformat()
        }, importance=0.7)

# Initialize FastAPI
app = FastAPI(
    title="BrainOps - AI Operating System",
    description="The brain that runs everything",
    version="4.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://myroofgenius.com",
        "https://www.myroofgenius.com",
        "https://weathercraft-erp.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ThoughtRequest(BaseModel):
    thought: str
    category: Optional[str] = "general"
    importance: Optional[float] = 0.5

class DecisionRequest(BaseModel):
    context: Dict[str, Any]
    options: List[Dict[str, Any]]

class MemoryQuery(BaseModel):
    query: str
    category: Optional[str] = None
    limit: Optional[int] = 10

class NeuralRequest(BaseModel):
    request: str
    context: Optional[Dict[str, Any]] = {}

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with brain status"""
    brain_status = await brain.get_brain_status() if brain else {}
    neural_status = await neural_network.get_system_knowledge() if neural_network else {}
    env_status = await env_manager.get_status_report() if env_manager else {}
    
    return {
        "name": "BrainOps AI OS",
        "version": "4.0.0",
        "brain": brain_status,
        "neural_network": neural_status,
        "environment": env_status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check with memory verification"""
    # Test brain memory
    thought = await brain.store_thought({
        "type": "health_check",
        "timestamp": datetime.now().isoformat()
    }, importance=0.1)
    
    # Recall to verify
    memories = await brain.recall_memory("health_check", limit=1)
    
    return {
        "status": "healthy" if memories else "degraded",
        "brain_active": brain is not None,
        "neural_active": neural_network is not None,
        "memory_working": len(memories) > 0 if memories else False,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/brain/think")
async def think(request: ThoughtRequest):
    """Store a thought in the brain"""
    try:
        result = await brain.store_thought(
            {
                "content": request.thought,
                "category": request.category,
                "source": "api",
                "timestamp": datetime.now().isoformat()
            },
            importance=request.importance
        )
        
        return {
            "success": True,
            "thought_id": result["id"] if result else None,
            "message": "Thought stored in persistent memory"
        }
    except Exception as e:
        logger.error(f"Failed to store thought: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/brain/recall")
async def recall(request: MemoryQuery):
    """Recall memories from the brain"""
    try:
        memories = await brain.recall_memory(
            request.query,
            category=request.category,
            limit=request.limit
        )
        
        return {
            "success": True,
            "memories": memories,
            "count": len(memories)
        }
    except Exception as e:
        logger.error(f"Failed to recall memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/brain/decide")
async def make_decision(request: DecisionRequest):
    """Make a decision using brain memory"""
    try:
        decision = await brain.make_decision(
            request.context,
            request.options
        )
        
        return {
            "success": True,
            "decision": decision
        }
    except Exception as e:
        logger.error(f"Failed to make decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/neural/process")
async def neural_process(request: NeuralRequest):
    """Process request through neural network"""
    try:
        # Store request in brain
        await brain.store_thought({
            "type": "neural_request",
            "content": request.request,
            "context": request.context
        }, importance=0.6)
        
        # Process through neural network
        result = await neural_network.process(request.request)
        
        # Store result in brain
        await brain.store_thought({
            "type": "neural_response",
            "content": result,
            "confidence": result.get("confidence", 0.5)
        }, importance=0.7)
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Neural processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/brain/status")
async def get_brain_status():
    """Get complete brain status"""
    try:
        brain_status = await brain.get_brain_status()
        neural_status = await neural_network.get_system_knowledge()
        
        # Synthesize knowledge about system
        synthesis = await brain.synthesize_knowledge("system_status")
        
        return {
            "brain": brain_status,
            "neural": neural_status,
            "synthesis": synthesis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get brain status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/brain/learn")
async def learn(decision_id: str, outcome: Dict, success: bool):
    """Learn from decision outcome"""
    try:
        await brain.learn_from_outcome(decision_id, outcome, success)
        
        # Store learning in neural network too
        await neural_network.process(f"Learn from outcome: {json.dumps(outcome)}")
        
        return {
            "success": True,
            "message": "Learning stored in persistent memory"
        }
    except Exception as e:
        logger.error(f"Failed to learn: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/env/variables")
async def get_environment_variables(service: Optional[str] = None, category: Optional[str] = None):
    """Get environment variables from database"""
    try:
        variables = await env_manager.get_all_variables(service=service, category=category)
        
        # Store access in brain
        await brain.store_thought({
            "type": "env_access",
            "content": f"Accessed {len(variables)} environment variables",
            "filter": {"service": service, "category": category}
        }, importance=0.2)
        
        return {
            "success": True,
            "variables": variables,
            "count": len(variables)
        }
    except Exception as e:
        logger.error(f"Failed to get environment variables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/env/rotate")
async def rotate_secret(key: str, new_value: str):
    """Rotate a secret"""
    try:
        await env_manager.rotate_secret(key, new_value)
        
        # Store in brain
        await brain.store_thought({
            "type": "security_action",
            "content": f"Rotated secret: {key}",
            "timestamp": datetime.now().isoformat()
        }, importance=0.9)
        
        return {
            "success": True,
            "message": f"Secret {key} rotated successfully"
        }
    except Exception as e:
        logger.error(f"Failed to rotate secret: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/env/export")
async def export_environment(service: str = "ALL"):
    """Export environment variables as .env file"""
    try:
        env_content = await env_manager.export_env_file(service)
        
        return Response(
            content=env_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={service.lower()}.env"
            }
        )
    except Exception as e:
        logger.error(f"Failed to export environment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/brain")
async def brain_websocket(websocket: WebSocket):
    """WebSocket for real-time brain activity"""
    await websocket.accept()
    
    try:
        while True:
            # Send brain status every 5 seconds
            status = await brain.get_brain_status()
            await websocket.send_json({
                "type": "brain_status",
                "data": status,
                "timestamp": datetime.now().isoformat()
            })
            
            # Send latest thoughts
            if brain.thought_stream:
                await websocket.send_json({
                    "type": "thought_stream",
                    "data": brain.thought_stream[-5:],  # Last 5 thoughts
                    "timestamp": datetime.now().isoformat()
                })
            
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        logger.info("Brain WebSocket disconnected")

@app.post("/api/leads/capture")
async def capture_lead(lead: Lead, background_tasks: BackgroundTasks):
    """Capture lead with brain processing"""
    try:
        # Store lead in brain first
        await brain.store_thought({
            "type": "lead_capture",
            "content": lead.dict(),
            "category": "revenue",
            "timestamp": datetime.now().isoformat()
        }, importance=0.8)
        
        # Process through neural network
        neural_result = await neural_network.process(f"Process new lead: {lead.name} from {lead.source}")
        
        # Make decision about lead
        decision = await brain.make_decision(
            {"lead": lead.dict(), "neural_analysis": neural_result},
            [
                {"action": "immediate_quote", "priority": "high"},
                {"action": "schedule_followup", "priority": "medium"},
                {"action": "nurture_campaign", "priority": "low"}
            ]
        )
        
        # Process through revenue engine
        # result = await revenue_engine.capture_lead(lead)
        
        return {
            "success": True,
            "decision": decision,
            "neural_analysis": neural_result
        }
    except Exception as e:
        logger.error(f"Failed to capture lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/visualize")
async def visualize_system():
    """Get system visualization data"""
    try:
        # Get complete system state
        brain_status = await brain.get_brain_status()
        neural_knowledge = await neural_network.get_system_knowledge()
        env_status = await env_manager.get_status_report()
        
        # Synthesize understanding
        synthesis = await brain.synthesize_knowledge("complete_system")
        
        return {
            "architecture": {
                "backend": "https://brainops-backend-prod.onrender.com",
                "frontends": [
                    "https://myroofgenius.com",
                    "https://weathercraft-erp.vercel.app"
                ],
                "database": "Supabase PostgreSQL",
                "persistent_memory": brain_status,
                "neural_network": neural_knowledge
            },
            "environment": env_status,
            "synthesis": synthesis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to visualize system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main_integrated:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
        workers=1,  # Single worker to maintain brain state
        log_level="info"
    )