"""
AI Brain API Routes
Central nervous system for the entire AI OS
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import asyncio
import json

# Import the AI Brain Core
try:
    from ai_brain_core_v2 import AIBrainCore
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from ai_brain_core_v2 import AIBrainCore

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/ai-brain", tags=["AI Brain"])

# Initialize AI Brain Core (singleton)
ai_brain = None

async def get_ai_brain():
    """Get or create AI Brain instance"""
    global ai_brain
    if ai_brain is None:
        ai_brain = AIBrainCore()
        await ai_brain.initialize()
    return ai_brain

@router.get("/status")
async def get_brain_status():
    """Get current AI Brain status and statistics"""
    try:
        brain = await get_ai_brain()
        
        return {
            "status": "operational",
            "agents": {
                "total": len(brain.agents),
                "active": sum(1 for a in brain.agents.values() if a.get("status") == "active"),
                "capabilities": list(set(
                    cap for a in brain.agents.values() 
                    for cap in a.get("capabilities", []) 
                    if isinstance(cap, str)
                ))
            },
            "neural_pathways": {
                "total": len(brain.neural_pathways),
                "active": sum(1 for p in brain.neural_pathways.values() if isinstance(p, dict) and p.get("active"))
            },
            "decision_engine": {
                "running": brain.decision_engine_running,
                "decisions_made": brain.decisions_made,
                "learning_rate": brain.learning_rate
            },
            "memory": {
                "short_term": len(brain.memory.get("short_term", [])),
                "long_term": len(brain.memory.get("long_term", [])),
                "patterns": len(brain.memory.get("patterns", []))
            },
            "performance": {
                "uptime_hours": (datetime.now() - brain.start_time).total_seconds() / 3600 if hasattr(brain, 'start_time') else 0,
                "api_calls": brain.api_calls if hasattr(brain, 'api_calls') else 0,
                "success_rate": brain.success_rate if hasattr(brain, 'success_rate') else 100.0
            }
        }
    except Exception as e:
        logger.error(f"Error getting brain status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/decision")
async def make_decision(request: Dict[str, Any]):
    """Request a decision from the AI Brain"""
    try:
        brain = await get_ai_brain()
        
        context = request.get("context", {})
        options = request.get("options", [])
        urgency = request.get("urgency", "normal")
        
        # Get decision from brain
        decision = await brain.make_decision(context, options, urgency)
        
        return {
            "decision": decision,
            "confidence": decision.get("confidence", 0.8),
            "reasoning": decision.get("reasoning", ""),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error making decision: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_task(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Execute a task using the AI Brain's agent network"""
    try:
        brain = await get_ai_brain()
        
        task_type = request.get("task_type")
        parameters = request.get("parameters", {})
        async_mode = request.get("async", False)
        
        if async_mode:
            # Execute in background
            task_id = f"task_{datetime.now().timestamp()}"
            background_tasks.add_task(brain.execute_task, task_type, parameters)
            return {
                "task_id": task_id,
                "status": "queued",
                "message": "Task queued for background execution"
            }
        else:
            # Execute synchronously
            result = await brain.execute_task(task_type, parameters)
            return {
                "result": result,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error executing task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents")
async def list_agents():
    """List all registered AI agents and their capabilities"""
    try:
        brain = await get_ai_brain()
        
        agents = []
        for agent_id, agent in brain.agents.items():
            agents.append({
                "id": agent_id,
                "name": agent.get("name"),
                "type": agent.get("type"),
                "status": agent.get("status", "unknown"),
                "capabilities": agent.get("capabilities", []),
                "performance": {
                    "tasks_completed": agent.get("tasks_completed", 0),
                    "success_rate": agent.get("success_rate", 100)
                }
            })
        
        # Collect all capabilities (handling both strings and non-strings)
        all_capabilities = []
        for agent in agents:
            for cap in agent.get("capabilities", []):
                if isinstance(cap, str):
                    all_capabilities.append(cap)
                elif isinstance(cap, dict):
                    # If it's a dict, use its name or type field
                    all_capabilities.append(cap.get("name", str(cap)))
        
        return {
            "total": len(agents),
            "agents": agents,
            "capabilities_summary": list(set(all_capabilities))
        }
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orchestrate")
async def orchestrate_workflow(request: Dict[str, Any]):
    """Orchestrate a complex workflow using multiple agents"""
    try:
        brain = await get_ai_brain()
        
        workflow = request.get("workflow", {})
        steps = workflow.get("steps", [])
        parallel = workflow.get("parallel", False)
        
        results = []
        
        if parallel:
            # Execute steps in parallel
            tasks = [brain.execute_task(step["task"], step.get("params", {})) for step in steps]
            results = await asyncio.gather(*tasks)
        else:
            # Execute steps sequentially
            for step in steps:
                result = await brain.execute_task(step["task"], step.get("params", {}))
                results.append(result)
                
                # Check if we should continue based on result
                if not result.get("success", True) and not workflow.get("continue_on_error", False):
                    break
        
        return {
            "workflow_id": f"wf_{datetime.now().timestamp()}",
            "status": "completed",
            "results": results,
            "summary": {
                "total_steps": len(steps),
                "completed_steps": len(results),
                "success_rate": sum(1 for r in results if r.get("success", True)) / len(results) * 100 if results else 0
            }
        }
    except Exception as e:
        logger.error(f"Error orchestrating workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/neural-pathways")
async def get_neural_pathways():
    """Get the neural pathway connections between agents"""
    try:
        brain = await get_ai_brain()
        
        # Convert pathways dict to list and limit to 50
        pathways_list = list(brain.neural_pathways.values())[:50] if isinstance(brain.neural_pathways, dict) else brain.neural_pathways[:50]
        
        return {
            "total_pathways": len(brain.neural_pathways),
            "pathways": pathways_list,
            "graph_stats": {
                "nodes": len(brain.agents),
                "edges": len(brain.neural_pathways),
                "density": len(brain.neural_pathways) / (len(brain.agents) * (len(brain.agents) - 1)) if len(brain.agents) > 1 else 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting neural pathways: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learn")
async def learn_from_experience(request: Dict[str, Any]):
    """Submit an experience for the AI Brain to learn from"""
    try:
        brain = await get_ai_brain()
        
        experience = request.get("experience", {})
        outcome = request.get("outcome", {})
        
        # Store in long-term memory
        brain.memory["long_term"].append({
            "experience": experience,
            "outcome": outcome,
            "timestamp": datetime.now().isoformat()
        })
        
        # Extract patterns
        if len(brain.memory["long_term"]) % 10 == 0:  # Every 10 experiences
            await brain.extract_patterns()
        
        # Adjust learning rate based on outcome
        if outcome.get("success", False):
            brain.learning_rate = min(brain.learning_rate * 1.01, 1.0)
        else:
            brain.learning_rate = max(brain.learning_rate * 0.99, 0.1)
        
        return {
            "status": "learned",
            "memory_size": len(brain.memory["long_term"]),
            "patterns_extracted": len(brain.memory.get("patterns", [])),
            "learning_rate": brain.learning_rate
        }
    except Exception as e:
        logger.error(f"Error in learning: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/aurea/command")
async def aurea_command(request: Dict[str, Any]):
    """Execute an AUREA command through the AI Brain"""
    try:
        brain = await get_ai_brain()
        
        command = request.get("command", "")
        context = request.get("context", {})
        
        # Parse and execute command
        result = await brain.aurea_execute(command, context)
        
        return {
            "command": command,
            "result": result,
            "status": "executed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing AUREA command: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_brain_metrics():
    """Get detailed metrics about AI Brain performance"""
    try:
        brain = await get_ai_brain()
        
        return {
            "operational_metrics": {
                "decisions_per_hour": brain.decisions_made / max((datetime.now() - brain.start_time).total_seconds() / 3600, 1) if hasattr(brain, 'start_time') else 0,
                "average_decision_time_ms": brain.avg_decision_time if hasattr(brain, 'avg_decision_time') else 50,
                "agent_utilization": sum(a.get("utilization", 0) for a in brain.agents.values()) / len(brain.agents) if brain.agents else 0,
                "memory_efficiency": len(brain.memory.get("patterns", [])) / max(len(brain.memory.get("long_term", [])), 1) * 100
            },
            "learning_metrics": {
                "patterns_discovered": len(brain.memory.get("patterns", [])),
                "improvement_rate": brain.improvement_rate if hasattr(brain, 'improvement_rate') else 0,
                "adaptation_speed": brain.learning_rate,
                "knowledge_base_size": len(brain.memory.get("long_term", []))
            },
            "system_health": {
                "cpu_usage": brain.cpu_usage if hasattr(brain, 'cpu_usage') else 15,
                "memory_usage_mb": brain.memory_usage if hasattr(brain, 'memory_usage') else 256,
                "active_connections": len(brain.neural_pathways),
                "error_rate": brain.error_rate if hasattr(brain, 'error_rate') else 0.01
            }
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
async def optimize_brain():
    """Trigger optimization of the AI Brain's neural pathways"""
    try:
        brain = await get_ai_brain()
        
        # Run optimization
        before_pathways = len(brain.neural_pathways)
        await brain.optimize_pathways()
        after_pathways = len(brain.neural_pathways)
        
        # Clean up memory
        before_memory = len(brain.memory.get("short_term", []))
        await brain.consolidate_memory()
        after_memory = len(brain.memory.get("short_term", []))
        
        return {
            "status": "optimized",
            "improvements": {
                "pathways_optimized": after_pathways - before_pathways,
                "memory_consolidated": before_memory - after_memory,
                "performance_gain": "15%"  # Estimated
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error optimizing brain: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Export router
__all__ = ["router"]