"""
LangGraph Workflow Execution

Exposes workflow definitions stored in the database. Execution is intentionally
disabled until integrated with real agent tooling (no simulated outputs).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

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
async def execute_workflow(workflow_name: str, request: WorkflowExecutionRequest):
    """Execute a LangGraph workflow (disabled without real agent integration)."""
    raise HTTPException(
        status_code=501,
        detail="Workflow execution is not enabled on this server",
    )


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

