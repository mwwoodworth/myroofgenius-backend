"""
BrainOps AI OS - Unified API Routes

Comprehensive API endpoints for the BrainOps AI Operating System:
- Metacognitive Controller
- Continuous Awareness System
- Unified Memory Substrate
- Dynamic Neural Pathways
- Hierarchical Goal Architecture
- Closed-Loop Learning Pipeline
- Proactive Intelligence Engine
- Reasoning Engine
- Self-Optimization System

Version: 1.0.0
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field

from core.brain_store import build_brain_key, dispatch_brain_store

logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(prefix="/api/v1/brainops", tags=["BrainOps AI OS"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class MemoryStoreRequest(BaseModel):
    """Request to store a memory"""
    content: Dict[str, Any]
    memory_type: str = "working"  # working, episodic, semantic, procedural
    importance: float = 0.5
    context: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class MemorySearchRequest(BaseModel):
    """Request to search memory"""
    query: str
    memory_types: Optional[List[str]] = None
    limit: int = 10
    min_relevance: float = 0.5


class GoalCreateRequest(BaseModel):
    """Request to create a goal"""
    name: str
    description: str
    goal_type: str = "operational"  # strategic, tactical, operational
    parent_id: Optional[str] = None
    target_metrics: Optional[Dict[str, float]] = None
    deadline: Optional[datetime] = None


class ReasoningRequest(BaseModel):
    """Request for reasoning analysis"""
    query: str
    context: Optional[Dict[str, Any]] = None
    reasoning_type: str = "deductive"  # deductive, inductive, abductive, causal, analogical
    max_depth: int = 5


class LearningOutcomeRequest(BaseModel):
    """Request to record a learning outcome"""
    action: str
    outcome: str
    success: bool
    context: Optional[Dict[str, Any]] = None
    feedback_score: Optional[float] = None


class ProcessingRequest(BaseModel):
    """Request for brain processing"""
    input_data: Dict[str, Any]
    processing_type: str = "standard"  # standard, urgent, background
    context: Optional[Dict[str, Any]] = None


class SensorDataRequest(BaseModel):
    """Request to feed sensor data"""
    sensor_type: str
    data: Dict[str, Any]


# ============================================================================
# DEPENDENCY HELPERS
# ============================================================================

async def get_brainops_controller(request: Request):
    """Get the BrainOps controller from app state"""
    controller = getattr(request.app.state, 'brainops_controller', None)
    if not controller:
        raise HTTPException(
            status_code=503,
            detail="BrainOps AI OS not initialized"
        )
    return controller


async def get_db_pool(request: Request):
    """Get database pool from app state"""
    pool = getattr(request.app.state, 'db_pool', None)
    if not pool:
        raise HTTPException(
            status_code=503,
            detail="Database not available"
        )
    return pool


# ============================================================================
# SYSTEM STATUS & HEALTH
# ============================================================================

@router.get("/status")
async def get_system_status(request: Request):
    """
    Get comprehensive BrainOps AI OS status

    Returns the health and status of all subsystems
    """
    controller = getattr(request.app.state, 'brainops_controller', None)

    if not controller:
        return {
            "status": "offline",
            "message": "BrainOps AI OS not initialized",
            "subsystems": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    try:
        # Get comprehensive health from controller
        health = await controller.get_health()

        return {
            "status": health.get("status", "unknown"),
            "consciousness": {
                "state": controller.state.value if hasattr(controller, 'consciousness_state') else "unknown",
                "cycle_count": controller.metrics.get("consciousness_cycles", 0) if hasattr(controller, 'metrics') else 0
            },
            "subsystems": health.get("subsystems", {}),
            "metrics": health.get("metrics", {}),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting BrainOps status: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/health")
async def get_health(request: Request):
    """
    Quick health check for BrainOps AI OS
    """
    controller = getattr(request.app.state, 'brainops_controller', None)

    if not controller:
        return {"status": "offline", "healthy": False}

    try:
        health = await controller.get_health()
        return {
            "status": health.get("status", "unknown"),
            "healthy": health.get("status") == "healthy",
            "subsystem_health": {
                name: info.get("status") == "healthy"
                for name, info in health.get("subsystems", {}).items()
            }
        }
    except Exception as e:
        return {"status": "error", "healthy": False, "error": str(e)}


# ============================================================================
# METACOGNITIVE CONTROLLER
# ============================================================================

@router.post("/process")
async def process_input(
    request_data: ProcessingRequest,
    controller=Depends(get_brainops_controller)
):
    """
    Process input through the metacognitive controller

    The brain processes the input and returns a coordinated response
    using all subsystems (memory, reasoning, awareness, etc.)
    """
    try:
        result = await controller.process(
            request_data.input_data,
            context=request_data.context or {}
        )
        context = request_data.context or {}
        dispatch_brain_store(
            key=build_brain_key(
                scope="brainops_ai_os",
                action="process_input",
                tenant_id=str(context.get("tenant_id")) if isinstance(context, dict) else None,
            ),
            value={
                "processing_type": request_data.processing_type,
                "input_keys": sorted(request_data.input_data.keys())[:12],
                "context_keys": sorted(context.keys())[:12] if isinstance(context, dict) else [],
            },
            category="decisioning",
            priority="high" if request_data.processing_type == "urgent" else "medium",
        )
        return {
            "status": "processed",
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consciousness")
async def get_consciousness_state(controller=Depends(get_brainops_controller)):
    """
    Get current consciousness state

    Returns the current state of the metacognitive controller's
    consciousness loop (awake, dreaming, focused, etc.)
    """
    return {
        "state": controller.state.value if hasattr(controller, 'consciousness_state') else "unknown",
        "attention": {
            "current_focus": controller.current_attention if hasattr(controller, 'current_attention') else None,
            "active_thoughts": len(controller.current_thoughts) if hasattr(controller, 'active_thoughts') else 0
        },
        "metrics": {
            "cycles": controller.metrics.get("consciousness_cycles", 0) if hasattr(controller, 'metrics') else 0,
            "thoughts_processed": controller.metrics.get("thoughts_processed", 0) if hasattr(controller, 'metrics') else 0,
            "decisions_made": controller.metrics.get("decisions_made", 0) if hasattr(controller, 'metrics') else 0
        }
    }


@router.post("/reflect")
async def trigger_reflection(
    topic: Optional[str] = None,
    controller=Depends(get_brainops_controller)
):
    """
    Trigger a self-reflection cycle

    The brain reflects on recent activities, learning, and performance
    """
    try:
        reflection = await controller.reflect(topic=topic)
        dispatch_brain_store(
            key=build_brain_key(scope="brainops_ai_os", action="reflection"),
            value={
                "topic": topic or "general",
                "reflection_type": "manual_trigger",
            },
            category="learning",
            priority="medium",
        )
        return {
            "status": "reflected",
            "reflection": reflection,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Reflection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UNIFIED MEMORY SYSTEM
# ============================================================================

@router.post("/memory/store")
async def store_memory(
    memory_request: MemoryStoreRequest,
    controller=Depends(get_brainops_controller)
):
    """
    Store information in the unified memory system

    Supports working, episodic, semantic, and procedural memory types
    """
    try:
        if not controller.unified_memory:
            raise HTTPException(status_code=503, detail="Memory system not available")

        memory_id = await controller.unified_memory.store(
            content=memory_request.content,
            memory_type=memory_request.memory_type,
            importance=memory_request.importance,
            context=memory_request.context,
            tags=memory_request.tags
        )

        context = memory_request.context or {}
        dispatch_brain_store(
            key=build_brain_key(
                scope="brainops_ai_os",
                action="memory_stored",
                tenant_id=str(context.get("tenant_id")) if isinstance(context, dict) else None,
            ),
            value={
                "memory_id": memory_id,
                "memory_type": memory_request.memory_type,
                "importance": memory_request.importance,
                "tag_count": len(memory_request.tags or []),
                "content_keys": sorted(memory_request.content.keys())[:12],
            },
            category="memory",
            priority="high" if memory_request.importance >= 0.8 else "medium",
        )

        return {
            "status": "stored",
            "memory_id": memory_id,
            "type": memory_request.memory_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory storage error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/search")
async def search_memory(
    search_request: MemorySearchRequest,
    controller=Depends(get_brainops_controller)
):
    """
    Search the unified memory using semantic similarity

    Uses vector embeddings for intelligent semantic search
    """
    try:
        if not controller.unified_memory:
            raise HTTPException(status_code=503, detail="Memory system not available")

        results = await controller.unified_memory.search(
            query=search_request.query,
            memory_types=search_request.memory_types,
            limit=search_request.limit,
            min_relevance=search_request.min_relevance
        )

        return {
            "query": search_request.query,
            "results": results,
            "count": len(results),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/recall/{memory_id}")
async def recall_memory(
    memory_id: str,
    controller=Depends(get_brainops_controller)
):
    """
    Recall a specific memory by ID
    """
    try:
        if not controller.unified_memory:
            raise HTTPException(status_code=503, detail="Memory system not available")

        memory = await controller.unified_memory.recall(memory_id)

        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        return memory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory recall error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/consolidate")
async def trigger_memory_consolidation(
    background_tasks: BackgroundTasks,
    controller=Depends(get_brainops_controller)
):
    """
    Trigger memory consolidation process

    Moves important working memories to long-term storage
    and synthesizes patterns
    """
    try:
        if not controller.unified_memory:
            raise HTTPException(status_code=503, detail="Memory system not available")

        # Run consolidation in background
        background_tasks.add_task(controller.unified_memory.consolidate_memories)

        return {
            "status": "consolidation_started",
            "message": "Memory consolidation running in background",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory consolidation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/stats")
async def get_memory_stats(controller=Depends(get_brainops_controller)):
    """
    Get unified memory system statistics
    """
    try:
        if not controller.unified_memory:
            raise HTTPException(status_code=503, detail="Memory system not available")

        health = await controller.unified_memory.get_health()
        return health
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AWARENESS SYSTEM
# ============================================================================

@router.get("/awareness/status")
async def get_awareness_status(controller=Depends(get_brainops_controller)):
    """
    Get current awareness system status

    Shows active sensors, recent readings, and alerts
    """
    try:
        if not controller.awareness_system:
            raise HTTPException(status_code=503, detail="Awareness system not available")

        health = await controller.awareness_system.get_health()
        return health
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Awareness status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/awareness/sensor")
async def feed_sensor_data(
    sensor_data: SensorDataRequest,
    controller=Depends(get_brainops_controller)
):
    """
    Feed external sensor data into the awareness system
    """
    try:
        if not controller.awareness_system:
            raise HTTPException(status_code=503, detail="Awareness system not available")

        await controller.awareness_system.feed_sensor_data(
            sensor_type=sensor_data.sensor_type,
            data=sensor_data.data
        )

        return {
            "status": "received",
            "sensor_type": sensor_data.sensor_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sensor data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/awareness/alerts")
async def get_active_alerts(
    severity: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    controller=Depends(get_brainops_controller)
):
    """
    Get active alerts from the awareness system
    """
    try:
        if not controller.awareness_system:
            raise HTTPException(status_code=503, detail="Awareness system not available")

        alerts = await controller.awareness_system.get_alerts(
            severity=severity,
            limit=limit
        )

        return {
            "alerts": alerts,
            "count": len(alerts),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Alerts retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/awareness/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    controller=Depends(get_brainops_controller)
):
    """
    Acknowledge an alert
    """
    try:
        if not controller.awareness_system:
            raise HTTPException(status_code=503, detail="Awareness system not available")

        await controller.awareness_system.acknowledge_alert(alert_id)

        return {
            "status": "acknowledged",
            "alert_id": alert_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Alert acknowledgment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEURAL DYNAMICS
# ============================================================================

@router.get("/neural/status")
async def get_neural_status(controller=Depends(get_brainops_controller)):
    """
    Get neural network status including active pathways and clusters
    """
    try:
        if not controller.neural_network:
            raise HTTPException(status_code=503, detail="Neural network not available")

        health = await controller.neural_network.get_health()
        return health
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Neural status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/neural/activate")
async def activate_neurons(
    pattern: str,
    context: Optional[Dict[str, Any]] = None,
    controller=Depends(get_brainops_controller)
):
    """
    Activate neural pattern for routing or processing

    Uses Hebbian learning to strengthen connections
    """
    try:
        if not controller.neural_network:
            raise HTTPException(status_code=503, detail="Neural network not available")

        result = await controller.neural_network.activate(
            pattern=pattern,
            context=context or {}
        )

        return {
            "status": "activated",
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Neural activation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/neural/pathways")
async def get_neural_pathways(
    min_strength: float = Query(0.5, ge=0, le=1),
    limit: int = Query(100, ge=1, le=500),
    controller=Depends(get_brainops_controller)
):
    """
    Get active neural pathways (strong synaptic connections)
    """
    try:
        if not controller.neural_network:
            raise HTTPException(status_code=503, detail="Neural network not available")

        pathways = await controller.neural_network.get_pathways(
            min_strength=min_strength,
            limit=limit
        )

        return {
            "pathways": pathways,
            "count": len(pathways),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pathways retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/neural/clusters")
async def get_neural_clusters(controller=Depends(get_brainops_controller)):
    """
    Get emergent neural clusters (groups of frequently co-activated neurons)
    """
    try:
        if not controller.neural_network:
            raise HTTPException(status_code=503, detail="Neural network not available")

        clusters = await controller.neural_network.get_clusters()

        return {
            "clusters": clusters,
            "count": len(clusters),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clusters retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GOAL ARCHITECTURE
# ============================================================================

@router.post("/goals")
async def create_goal(
    goal_request: GoalCreateRequest,
    controller=Depends(get_brainops_controller)
):
    """
    Create a new goal in the hierarchical goal system
    """
    try:
        if not controller.goal_architecture:
            raise HTTPException(status_code=503, detail="Goal architecture not available")

        goal_id = await controller.goal_architecture.create_goal(
            name=goal_request.name,
            description=goal_request.description,
            goal_type=goal_request.goal_type,
            parent_id=goal_request.parent_id,
            target_metrics=goal_request.target_metrics,
            deadline=goal_request.deadline
        )

        dispatch_brain_store(
            key=build_brain_key(scope="brainops_ai_os", action="goal_created"),
            value={
                "goal_id": goal_id,
                "goal_name": goal_request.name,
                "goal_type": goal_request.goal_type,
                "has_parent": goal_request.parent_id is not None,
                "has_deadline": goal_request.deadline is not None,
            },
            category="planning",
            priority="high" if goal_request.goal_type == "strategic" else "medium",
        )

        return {
            "status": "created",
            "goal_id": goal_id,
            "type": goal_request.goal_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Goal creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/goals")
async def list_goals(
    goal_type: Optional[str] = None,
    status: Optional[str] = None,
    parent_id: Optional[str] = None,
    controller=Depends(get_brainops_controller)
):
    """
    List goals with optional filtering
    """
    try:
        if not controller.goal_architecture:
            raise HTTPException(status_code=503, detail="Goal architecture not available")

        goals = await controller.goal_architecture.list_goals(
            goal_type=goal_type,
            status=status,
            parent_id=parent_id
        )

        return {
            "goals": goals,
            "count": len(goals),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Goal listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/goals/{goal_id}")
async def get_goal(
    goal_id: str,
    controller=Depends(get_brainops_controller)
):
    """
    Get a specific goal with its progress and sub-goals
    """
    try:
        if not controller.goal_architecture:
            raise HTTPException(status_code=503, detail="Goal architecture not available")

        goal = await controller.goal_architecture.get_goal(goal_id)

        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

        return goal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Goal retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/goals/{goal_id}/progress")
async def update_goal_progress(
    goal_id: str,
    progress: float = Query(..., ge=0, le=1),
    notes: Optional[str] = None,
    controller=Depends(get_brainops_controller)
):
    """
    Update progress on a goal
    """
    try:
        if not controller.goal_architecture:
            raise HTTPException(status_code=503, detail="Goal architecture not available")

        await controller.goal_architecture.update_progress(
            goal_id=goal_id,
            progress=progress,
            notes=notes
        )

        return {
            "status": "updated",
            "goal_id": goal_id,
            "progress": progress,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Goal progress update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/goals/{goal_id}/decompose")
async def decompose_goal(
    goal_id: str,
    background_tasks: BackgroundTasks,
    controller=Depends(get_brainops_controller)
):
    """
    Use AI to decompose a goal into sub-goals
    """
    try:
        if not controller.goal_architecture:
            raise HTTPException(status_code=503, detail="Goal architecture not available")

        # Run decomposition in background
        background_tasks.add_task(
            controller.goal_architecture.ai_decompose_goal,
            goal_id
        )

        return {
            "status": "decomposition_started",
            "goal_id": goal_id,
            "message": "AI goal decomposition running in background",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Goal decomposition error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REASONING ENGINE
# ============================================================================

@router.post("/reasoning/analyze")
async def analyze_with_reasoning(
    reasoning_request: ReasoningRequest,
    controller=Depends(get_brainops_controller)
):
    """
    Perform chain-of-thought reasoning analysis

    Supports deductive, inductive, abductive, causal, and analogical reasoning
    """
    try:
        if not controller.reasoning_engine:
            raise HTTPException(status_code=503, detail="Reasoning engine not available")

        result = await controller.reasoning_engine.reason(
            query=reasoning_request.query,
            context=reasoning_request.context,
            reasoning_type=reasoning_request.reasoning_type,
            max_depth=reasoning_request.max_depth
        )

        return {
            "query": reasoning_request.query,
            "reasoning_type": reasoning_request.reasoning_type,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reasoning analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reasoning/decision")
async def analyze_decision(
    decision: str,
    options: List[str],
    context: Optional[Dict[str, Any]] = None,
    controller=Depends(get_brainops_controller)
):
    """
    Analyze a decision with multiple options

    Returns pros, cons, and recommendations for each option
    """
    try:
        if not controller.reasoning_engine:
            raise HTTPException(status_code=503, detail="Reasoning engine not available")

        result = await controller.reasoning_engine.analyze_decision(
            decision=decision,
            options=options,
            context=context
        )

        dispatch_brain_store(
            key=build_brain_key(
                scope="brainops_ai_os",
                action="decision_analyzed",
                tenant_id=str(context.get("tenant_id")) if isinstance(context, dict) else None,
            ),
            value={
                "decision": decision,
                "option_count": len(options),
                "context_keys": sorted(context.keys())[:12] if isinstance(context, dict) else [],
            },
            category="decisioning",
            priority="high" if len(options) > 3 else "medium",
        )

        return {
            "decision": decision,
            "analysis": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Decision analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reasoning/history")
async def get_reasoning_history(
    limit: int = Query(20, ge=1, le=100),
    controller=Depends(get_brainops_controller)
):
    """
    Get recent reasoning chains
    """
    try:
        if not controller.reasoning_engine:
            raise HTTPException(status_code=503, detail="Reasoning engine not available")

        history = await controller.reasoning_engine.get_history(limit=limit)

        return {
            "history": history,
            "count": len(history),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reasoning history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LEARNING PIPELINE
# ============================================================================

@router.post("/learning/outcome")
async def record_learning_outcome(
    outcome_request: LearningOutcomeRequest,
    controller=Depends(get_brainops_controller)
):
    """
    Record a learning outcome for closed-loop learning

    The system learns from successes and failures to improve
    """
    try:
        if not controller.learning_pipeline:
            raise HTTPException(status_code=503, detail="Learning pipeline not available")

        outcome_id = await controller.learning_pipeline.record_outcome(
            action=outcome_request.action,
            outcome=outcome_request.outcome,
            success=outcome_request.success,
            context=outcome_request.context,
            feedback_score=outcome_request.feedback_score
        )

        return {
            "status": "recorded",
            "outcome_id": outcome_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Learning outcome error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/patterns")
async def get_learned_patterns(
    pattern_type: Optional[str] = None,
    min_confidence: float = Query(0.7, ge=0, le=1),
    limit: int = Query(50, ge=1, le=200),
    controller=Depends(get_brainops_controller)
):
    """
    Get patterns learned from outcomes
    """
    try:
        if not controller.learning_pipeline:
            raise HTTPException(status_code=503, detail="Learning pipeline not available")

        patterns = await controller.learning_pipeline.get_patterns(
            pattern_type=pattern_type,
            min_confidence=min_confidence,
            limit=limit
        )

        return {
            "patterns": patterns,
            "count": len(patterns),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pattern retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/suggestions")
async def get_learning_suggestions(
    controller=Depends(get_brainops_controller)
):
    """
    Get AI-generated suggestions for improvement based on learning
    """
    try:
        if not controller.learning_pipeline:
            raise HTTPException(status_code=503, detail="Learning pipeline not available")

        suggestions = await controller.learning_pipeline.get_suggestions()

        return {
            "suggestions": suggestions,
            "count": len(suggestions),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Suggestions retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/stats")
async def get_learning_stats(controller=Depends(get_brainops_controller)):
    """
    Get learning pipeline statistics
    """
    try:
        if not controller.learning_pipeline:
            raise HTTPException(status_code=503, detail="Learning pipeline not available")

        health = await controller.learning_pipeline.get_health()
        return health
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Learning stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROACTIVE INTELLIGENCE
# ============================================================================

@router.get("/proactive/opportunities")
async def get_opportunities(
    opportunity_type: Optional[str] = None,
    min_score: float = Query(0.6, ge=0, le=1),
    limit: int = Query(20, ge=1, le=100),
    controller=Depends(get_brainops_controller)
):
    """
    Get detected opportunities

    The proactive engine scans for revenue, efficiency,
    customer, and risk opportunities
    """
    try:
        if not controller.proactive_engine:
            raise HTTPException(status_code=503, detail="Proactive engine not available")

        opportunities = await controller.proactive_engine.get_opportunities(
            opportunity_type=opportunity_type,
            min_score=min_score,
            limit=limit
        )

        return {
            "opportunities": opportunities,
            "count": len(opportunities),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Opportunities retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proactive/predictions")
async def get_predictions(
    prediction_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    controller=Depends(get_brainops_controller)
):
    """
    Get AI-generated predictions

    Includes churn risk, revenue forecasts, demand predictions
    """
    try:
        if not controller.proactive_engine:
            raise HTTPException(status_code=503, detail="Proactive engine not available")

        predictions = await controller.proactive_engine.get_predictions(
            prediction_type=prediction_type,
            limit=limit
        )

        return {
            "predictions": predictions,
            "count": len(predictions),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Predictions retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proactive/insights")
async def get_insights(
    limit: int = Query(20, ge=1, le=100),
    controller=Depends(get_brainops_controller)
):
    """
    Get proactive insights generated from data analysis
    """
    try:
        if not controller.proactive_engine:
            raise HTTPException(status_code=503, detail="Proactive engine not available")

        insights = await controller.proactive_engine.get_insights(limit=limit)

        return {
            "insights": insights,
            "count": len(insights),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Insights retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proactive/scan")
async def trigger_proactive_scan(
    background_tasks: BackgroundTasks,
    scan_type: Optional[str] = None,
    controller=Depends(get_brainops_controller)
):
    """
    Manually trigger a proactive scanning cycle
    """
    try:
        if not controller.proactive_engine:
            raise HTTPException(status_code=503, detail="Proactive engine not available")

        # Run scan in background
        background_tasks.add_task(
            controller.proactive_engine.scan,
            scan_type
        )

        return {
            "status": "scan_started",
            "scan_type": scan_type or "all",
            "message": "Proactive scan running in background",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Proactive scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SELF-OPTIMIZATION
# ============================================================================

@router.get("/optimization/status")
async def get_optimization_status(controller=Depends(get_brainops_controller)):
    """
    Get self-optimization system status
    """
    try:
        if not controller.self_optimization:
            raise HTTPException(status_code=503, detail="Self-optimization not available")

        health = await controller.self_optimization.get_health()
        return health
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Optimization status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimization/optimize")
async def trigger_optimization(
    component: str,
    background_tasks: BackgroundTasks,
    controller=Depends(get_brainops_controller)
):
    """
    Manually trigger optimization of a specific component

    Components: memory, database, cache, performance
    """
    try:
        if not controller.self_optimization:
            raise HTTPException(status_code=503, detail="Self-optimization not available")

        # Run optimization in background
        background_tasks.add_task(
            controller.self_optimization.optimize_component,
            component
        )

        dispatch_brain_store(
            key=build_brain_key(scope="brainops_ai_os", action="optimization_started"),
            value={
                "component": component,
                "trigger": "manual",
            },
            category="optimization",
            priority="high" if component in {"performance", "database"} else "medium",
        )

        return {
            "status": "optimization_started",
            "component": component,
            "message": f"Optimization of {component} running in background",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Optimization trigger error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/optimization/history")
async def get_optimization_history(
    optimization_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    request: Request = None
):
    """
    Get history of applied optimizations
    """
    try:
        pool = await get_db_pool(request)

        async with pool.acquire() as conn:
            if optimization_type:
                rows = await conn.fetch('''
                    SELECT optimization_id, optimization_type, description, target,
                           before_state, after_state, improvement, status, created_at, completed_at
                    FROM brainops_optimizations
                    WHERE optimization_type = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                ''', optimization_type, limit)
            else:
                rows = await conn.fetch('''
                    SELECT optimization_id, optimization_type, description, target,
                           before_state, after_state, improvement, status, created_at, completed_at
                    FROM brainops_optimizations
                    ORDER BY created_at DESC
                    LIMIT $1
                ''', limit)

        optimizations = [dict(row) for row in rows]

        return {
            "optimizations": optimizations,
            "count": len(optimizations),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Optimization history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ADMIN & DIAGNOSTICS
# ============================================================================

@router.get("/diagnostics")
async def get_diagnostics(controller=Depends(get_brainops_controller)):
    """
    Get comprehensive diagnostics for the BrainOps AI OS
    """
    try:
        health = await controller.get_health()

        return {
            "system_health": health,
            "version": "1.0.0",
            "uptime": controller.metrics.get("uptime_seconds", 0) if hasattr(controller, 'metrics') else 0,
            "subsystem_details": {
                "metacognitive": {
                    "consciousness_state": controller.state.value if hasattr(controller, 'consciousness_state') else "unknown",
                    "active_thoughts": len(controller.current_thoughts) if hasattr(controller, 'active_thoughts') else 0
                },
                "memory": await controller.unified_memory.get_health() if controller.unified_memory else {"status": "unavailable"},
                "awareness": await controller.awareness_system.get_health() if controller.awareness_system else {"status": "unavailable"},
                "neural": await controller.neural_network.get_health() if controller.neural_network else {"status": "unavailable"},
                "goals": await controller.goal_architecture.get_health() if controller.goal_architecture else {"status": "unavailable"},
                "learning": await controller.learning_pipeline.get_health() if controller.learning_pipeline else {"status": "unavailable"},
                "proactive": await controller.proactive_engine.get_health() if controller.proactive_engine else {"status": "unavailable"},
                "reasoning": await controller.reasoning_engine.get_health() if controller.reasoning_engine else {"status": "unavailable"},
                "optimization": await controller.self_optimization.get_health() if controller.self_optimization else {"status": "unavailable"}
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Diagnostics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_system(
    component: Optional[str] = None,
    controller=Depends(get_brainops_controller)
):
    """
    Reset a specific component or the entire system

    Use with caution - this clears runtime state
    """
    try:
        if component:
            await controller.reset_component(component)
            message = f"Reset {component} component"
        else:
            await controller.reset()
            message = "Full system reset completed"

        dispatch_brain_store(
            key=build_brain_key(scope="brainops_ai_os", action="system_reset"),
            value={
                "component": component or "all",
                "message": message,
            },
            category="operational",
            priority="high",
        )

        return {
            "status": "reset",
            "component": component or "all",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
