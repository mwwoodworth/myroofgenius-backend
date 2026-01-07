"""
LangGraph Workflow Execution

Exposes workflow definitions stored in the database and executes via the
production LangGraph orchestrator (no simulated outputs).
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict, Optional

import httpx

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/langgraph", tags=["LangGraph Workflows"])

try:
    from langgraph.graph import StateGraph  # noqa: F401

    LANGGRAPH_AVAILABLE = True
except Exception:
    LANGGRAPH_AVAILABLE = False


class WorkflowExecutionRequest(BaseModel):
    workflow_name: str
    input_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = {}


@router.get("/workflows")
def list_workflows(db: Session = Depends(get_db)):
    """List active workflow definitions."""
    try:
        result = db.execute(
            text(
                """
                SELECT
                    id, name, description, graph_type, status,
                    jsonb_array_length(nodes) as node_count,
                    jsonb_array_length(edges) as edge_count,
                    execution_count, success_rate,
                    created_at
                FROM langgraph_workflows
                WHERE status = 'active'
                ORDER BY created_at DESC
                """
            )
        )
        workflows = []
        for row in result:
            workflows.append(
                {
                    "id": str(row[0]),
                    "name": row[1],
                    "description": row[2],
                    "graph_type": row[3],
                    "status": row[4],
                    "node_count": row[5],
                    "edge_count": row[6],
                    "execution_count": row[7],
                    "success_rate": row[8],
                    "created_at": row[9].isoformat() if row[9] else None,
                }
            )

        return {
            "workflows": workflows,
            "total": len(workflows),
            "langgraph_available": LANGGRAPH_AVAILABLE,
        }
    except Exception as exc:
        message = str(exc).lower()
        if "does not exist" in message or "undefinedtable" in message:
            return {"workflows": [], "total": 0, "langgraph_available": LANGGRAPH_AVAILABLE}
        logger.exception("Error listing LangGraph workflows: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list workflows") from exc


@router.get("/workflows/{workflow_name}")
def get_workflow(workflow_name: str, db: Session = Depends(get_db)):
    """Get detailed workflow configuration."""
    try:
        row = db.execute(
            text(
                """
                SELECT
                    id, name, description, graph_type, graph_definition,
                    nodes, edges, conditional_edges, entry_point, status
                FROM langgraph_workflows
                WHERE name = :name AND status = 'active'
                """
            ),
            {"name": workflow_name},
        ).first()

        if not row:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_name} not found")

        return {
            "id": str(row[0]),
            "name": row[1],
            "description": row[2],
            "graph_type": row[3],
            "graph_definition": row[4],
            "nodes": row[5],
            "edges": row[6],
            "conditional_edges": row[7],
            "entry_point": row[8],
            "status": row[9],
        }
    except HTTPException:
        raise
    except Exception as exc:
        message = str(exc).lower()
        if "does not exist" in message or "undefinedtable" in message:
            raise HTTPException(status_code=503, detail="Workflow storage is not available") from exc
        logger.exception("Error getting workflow %s: %s", workflow_name, exc)
        raise HTTPException(status_code=500, detail="Failed to get workflow") from exc


@router.post("/workflows/{workflow_name}/execute")
async def execute_workflow(
    workflow_name: str,
    request: WorkflowExecutionRequest,
    db: Session = Depends(get_db),
):
    """Execute a LangGraph workflow using the production AI agents service."""
    ai_agents_url = os.getenv("BRAINOPS_AI_AGENTS_URL")
    api_key = os.getenv("BRAINOPS_API_KEY")

    if not ai_agents_url or not api_key:
        raise HTTPException(status_code=503, detail="LangGraph execution requires BRAINOPS_AI_AGENTS_URL and BRAINOPS_API_KEY")

    execution_id = str(uuid.uuid4())

    workflow = db.execute(
        text(
            """
            SELECT id, execution_count, success_rate
            FROM langgraph_workflows
            WHERE name = :name AND status = 'active'
            """
        ),
        {"name": workflow_name},
    ).first()

    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_name} not found")

    db.execute(
        text(
            """
            INSERT INTO langgraph_executions
            (id, workflow_id, execution_id, status, context, started_at, created_at)
            VALUES (:id, :workflow_id, :execution_id, 'running', :context, NOW(), NOW())
            """
        ),
        {
            "id": execution_id,
            "workflow_id": workflow[0],
            "execution_id": f"exec_{execution_id[:8]}",
            "context": {
                "workflow_name": workflow_name,
                "input_data": request.input_data,
                "context": request.context or {},
            },
        },
    )
    db.commit()

    payload = {
        "prompt": (
            f"Execute workflow '{workflow_name}' with input:\n"
            f"{request.input_data}\n"
            f"Context:\n{request.context}"
        ),
        "metadata": {
            "workflow_name": workflow_name,
            "input_data": request.input_data,
            "context": request.context or {},
            "execution_id": execution_id,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{ai_agents_url}/langgraph/workflow",
                headers={"X-API-Key": api_key},
                json=payload,
            )
    except Exception as exc:
        db.execute(
            text(
                """
                UPDATE langgraph_executions
                SET status = 'failed', error = :error, completed_at = NOW()
                WHERE id = :id
                """
            ),
            {"id": execution_id, "error": str(exc)},
        )
        db.commit()
        raise HTTPException(status_code=502, detail="LangGraph execution failed") from exc

    if response.status_code != 200:
        db.execute(
            text(
                """
                UPDATE langgraph_executions
                SET status = 'failed', error = :error, completed_at = NOW()
                WHERE id = :id
                """
            ),
            {"id": execution_id, "error": response.text[:500]},
        )
        db.commit()
        raise HTTPException(status_code=502, detail="LangGraph execution failed")

    result = response.json()
    success = result.get("status") not in {"failed", "error"}

    db.execute(
        text(
            """
            UPDATE langgraph_executions
            SET status = :status, result = :result, completed_at = NOW()
            WHERE id = :id
            """
        ),
        {
            "id": execution_id,
            "status": "completed" if success else "failed",
            "result": result,
        },
    )

    # Update workflow metrics
    current_count = workflow[1] or 0
    current_rate = workflow[2] or 0
    new_total = current_count + 1
    new_rate = ((current_rate * current_count) + (100 if success else 0)) / new_total
    db.execute(
        text(
            """
            UPDATE langgraph_workflows
            SET execution_count = :count, success_rate = :rate
            WHERE id = :id
            """
        ),
        {"id": workflow[0], "count": new_total, "rate": new_rate},
    )
    db.commit()

    return {
        "execution_id": execution_id,
        "workflow_name": workflow_name,
        "status": "completed" if success else "failed",
        "result": result,
    }


@router.get("/status")
def get_langgraph_status(db: Session = Depends(get_db)):
    """Get LangGraph system status (DB-backed)."""
    totals = {"total": None, "total_executions": None, "avg_success_rate": None}
    try:
        row = db.execute(
            text(
                """
                SELECT
                    COUNT(*) as total_workflows,
                    COALESCE(SUM(execution_count), 0) as total_executions,
                    AVG(success_rate) as avg_success_rate
                FROM langgraph_workflows
                WHERE status = 'active'
                """
            )
        ).first()
        if row:
            totals["total"] = int(row[0] or 0)
            totals["total_executions"] = int(row[1] or 0)
            totals["avg_success_rate"] = float(row[2]) if row[2] is not None else None
    except Exception:
        pass

    return {
        "langgraph_installed": LANGGRAPH_AVAILABLE,
        "status": "operational",
        "workflows": totals,
        "capabilities": {
            "state_graph": LANGGRAPH_AVAILABLE,
            "conditional_routing": LANGGRAPH_AVAILABLE,
        },
    }
