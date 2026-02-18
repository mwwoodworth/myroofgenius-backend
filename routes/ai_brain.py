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

from core.brain_store import build_brain_key, dispatch_brain_store, recall_context

# Import the AI Brain Core
try:
    from ai_brain_production import AIBrainProduction
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from ai_brain_production import AIBrainProduction

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/ai-brain", tags=["AI Brain"])

# Initialize AI Brain Core (singleton)
ai_brain = None

async def get_ai_brain():
    """Get or create AI Brain instance"""
    global ai_brain
    if ai_brain is None:
        ai_brain = AIBrainProduction()
        await ai_brain.initialize()
    return ai_brain

@router.get("/status")
async def get_brain_status():
    """Get current AI Brain status and statistics"""
    try:
        brain = await get_ai_brain()
        recalled_context = await recall_context(
            query="ai brain status operational context and recent memory health",
            limit=5,
        )

        short_term = getattr(brain, "short_term_memory", None)
        if short_term is None:
            short_term = brain.memory.get("short_term", []) if hasattr(brain, "memory") else []
        long_term = getattr(brain, "long_term_memory", None)
        if long_term is None:
            long_term = brain.memory.get("long_term", []) if hasattr(brain, "memory") else []
        patterns = brain.memory.get("patterns", []) if hasattr(brain, "memory") else []
        if not patterns and long_term:
            patterns = long_term

        return {
            "status": "operational",
            "agents": {
                "total": len(brain.agents),
                "active": sum(1 for a in brain.agents.values() if a.get("status") not in {"inactive", "offline"}),
                "capabilities": list(set(
                    cap for a in brain.agents.values() 
                    for cap in a.get("capabilities", []) 
                    if isinstance(cap, str)
                ))
            },
            "neural_pathways": {
                "total": len(brain.neural_pathways),
                "active": sum(1 for p in brain.neural_pathways.values() if isinstance(p, dict) and (p.get("strength") or 0) > 0)
            },
            "decision_engine": {
                "running": brain.decision_engine_running,
                "decisions_made": brain.decisions_made,
                "learning_rate": brain.learning_rate
            },
            "memory": {
                "short_term": len(short_term),
                "long_term": len(long_term),
                "patterns": len(patterns)
            },
            "performance": {
                "uptime_hours": (datetime.now() - brain.start_time).total_seconds() / 3600 if hasattr(brain, 'start_time') else 0,
                "api_calls": getattr(brain, "api_calls", getattr(brain, "tasks_executed", 0)),
                "success_rate": brain.success_rate if hasattr(brain, 'success_rate') else 100.0
            },
            "metadata": {
                "brain_context": recalled_context,
                "brain_context_count": len(recalled_context),
            },
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
        if not isinstance(context, dict):
            context = {}
        options = request.get("options", [])
        urgency = request.get("urgency", "normal")
        
        # Get decision from brain
        decision = await brain.make_decision(context, options, urgency)
        
        dispatch_brain_store(
            key=build_brain_key(
                scope="ai_brain",
                action="decision",
                tenant_id=context.get("tenant_id"),
            ),
            value={
                "urgency": urgency,
                "options_count": len(options) if isinstance(options, list) else 0,
                "context_keys": sorted(context.keys())[:12],
                "confidence": decision.get("confidence", 0.8),
            },
            category="decisioning",
            priority="high" if urgency in {"urgent", "high", "critical"} else "medium",
        )

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
            dispatch_brain_store(
                key=build_brain_key(
                    scope="ai_brain",
                    action="task_queued",
                    tenant_id=str(request.get("tenant_id") or "global"),
                ),
                value={
                    "task_type": task_type,
                    "async": True,
                    "parameter_keys": sorted(parameters.keys())[:12] if isinstance(parameters, dict) else [],
                },
                category="execution",
                priority="medium",
            )
            return {
                "task_id": task_id,
                "status": "queued",
                "message": "Task queued for background execution"
            }
        else:
            # Execute synchronously
            result = await brain.execute_task(task_type, parameters)
            dispatch_brain_store(
                key=build_brain_key(
                    scope="ai_brain",
                    action="task_executed",
                    tenant_id=str(request.get("tenant_id") or "global"),
                ),
                value={
                    "task_type": task_type,
                    "async": False,
                    "success": bool(result.get("success", True)) if isinstance(result, dict) else True,
                    "parameter_keys": sorted(parameters.keys())[:12] if isinstance(parameters, dict) else [],
                },
                category="execution",
                priority="medium",
            )
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
        
        workflow_id = f"wf_{datetime.now().timestamp()}"
        summary = {
            "total_steps": len(steps),
            "completed_steps": len(results),
            "success_rate": sum(1 for r in results if r.get("success", True)) / len(results) * 100 if results else 0,
        }

        dispatch_brain_store(
            key=build_brain_key(
                scope="ai_brain",
                action="workflow_orchestrated",
                tenant_id=str(request.get("tenant_id") or "global"),
            ),
            value={
                "parallel": bool(parallel),
                "summary": summary,
                "continue_on_error": bool(workflow.get("continue_on_error", False)),
            },
            category="orchestration",
            priority="high" if summary["success_rate"] < 100 else "medium",
        )

        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "results": results,
            "summary": summary
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
        if hasattr(brain, "long_term_memory"):
            brain.long_term_memory.append({
                "experience": experience,
                "outcome": outcome,
                "timestamp": datetime.now().isoformat()
            })
            memory_store = brain.long_term_memory
            patterns_store = getattr(brain, "long_term_memory", [])
        else:
            brain.memory["long_term"].append({
                "experience": experience,
                "outcome": outcome,
                "timestamp": datetime.now().isoformat()
            })
            memory_store = brain.memory.get("long_term", [])
            patterns_store = brain.memory.get("patterns", [])

        # Extract patterns
        if len(memory_store) % 10 == 0:  # Every 10 experiences
            await brain.extract_patterns()

        # Adjust learning rate based on outcome
        if outcome.get("success", False):
            brain.learning_rate = min(brain.learning_rate * 1.01, 1.0)
        else:
            brain.learning_rate = max(brain.learning_rate * 0.99, 0.1)

        dispatch_brain_store(
            key=build_brain_key(
                scope="ai_brain",
                action="learning_outcome",
                tenant_id=str(request.get("tenant_id") or "global"),
            ),
            value={
                "experience_keys": sorted(experience.keys())[:12] if isinstance(experience, dict) else [],
                "outcome_success": bool(outcome.get("success", False)) if isinstance(outcome, dict) else False,
                "memory_size": len(memory_store),
                "learning_rate": brain.learning_rate,
            },
            category="learning",
            priority="medium",
        )

        return {
            "status": "learned",
            "memory_size": len(memory_store),
            "patterns_extracted": len(patterns_store),
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

        short_term = getattr(brain, "short_term_memory", None)
        if short_term is None:
            short_term = brain.memory.get("short_term", []) if hasattr(brain, "memory") else []
        long_term = getattr(brain, "long_term_memory", None)
        if long_term is None:
            long_term = brain.memory.get("long_term", []) if hasattr(brain, "memory") else []
        patterns = brain.memory.get("patterns", []) if hasattr(brain, "memory") else []
        if not patterns and long_term:
            patterns = long_term

        cpu_usage = None
        memory_usage_mb = None
        try:
            import psutil
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage_mb = psutil.virtual_memory().used / (1024 * 1024)
        except Exception:
            pass

        return {
            "operational_metrics": {
                "decisions_per_hour": brain.decisions_made / max((datetime.now() - brain.start_time).total_seconds() / 3600, 1) if hasattr(brain, 'start_time') else 0,
                "average_decision_time_ms": getattr(brain, "working_memory", {}).get("last_decision_time") if hasattr(brain, "working_memory") else None,
                "agent_utilization": sum(a.get("utilization", 0) for a in brain.agents.values()) / len(brain.agents) if brain.agents else 0,
                "memory_efficiency": len(patterns) / max(len(long_term), 1) * 100
            },
            "learning_metrics": {
                "patterns_discovered": len(patterns),
                "improvement_rate": getattr(brain, "improvement_rate", None),
                "adaptation_speed": brain.learning_rate,
                "knowledge_base_size": len(long_term)
            },
            "system_health": {
                "cpu_usage": cpu_usage,
                "memory_usage_mb": memory_usage_mb,
                "active_connections": len(brain.neural_pathways),
                "error_rate": getattr(brain, "error_rate", None)
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
        before_memory = len(getattr(brain, "short_term_memory", brain.memory.get("short_term", []) if hasattr(brain, "memory") else []))
        await brain.consolidate_memory()
        after_memory = len(getattr(brain, "short_term_memory", brain.memory.get("short_term", []) if hasattr(brain, "memory") else []))
        
        dispatch_brain_store(
            key=build_brain_key(scope="ai_brain", action="optimized"),
            value={
                "pathways_optimized": after_pathways - before_pathways,
                "memory_consolidated": before_memory - after_memory,
            },
            category="optimization",
            priority="medium",
        )

        return {
            "status": "optimized",
            "improvements": {
                "pathways_optimized": after_pathways - before_pathways,
                "memory_consolidated": before_memory - after_memory,
                "performance_gain": None
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error optimizing brain: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Export router
__all__ = ["router"]
