"""
Marketing Automation Module - Task 79
Workflow automation and triggers
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import os
import httpx
import asyncpg
import uuid
import json

from core.supabase_auth import get_authenticated_user
from services.notifications import send_email_message, send_sms_message

router = APIRouter()

# Database connection
async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


async def _has_tenant_column(conn: asyncpg.Connection) -> bool:
    """Check if marketing_automations has tenant_id column."""
    return bool(await conn.fetchval(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'marketing_automations'
          AND column_name = 'tenant_id'
        LIMIT 1
        """
    ))


def _normalize_json(value, default):
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _evaluate_conditions(conditions: List[Dict[str, Any]], trigger_data: Dict[str, Any]) -> bool:
    """Evaluate automation conditions against trigger data."""
    if not conditions:
        return True

    for condition in conditions:
        field = condition.get("field")
        operator = (condition.get("operator") or "equals").lower()
        expected = condition.get("value")
        actual = trigger_data.get(field)

        if operator in {"equals", "=="} and actual != expected:
            return False
        if operator in {"not_equals", "!="} and actual == expected:
            return False
        if operator == "contains":
            if actual is None or str(expected) not in str(actual):
                return False
        if operator == "in":
            if actual not in (expected or []):
                return False
        if operator == "gt":
            try:
                if float(actual) <= float(expected):
                    return False
            except Exception:
                return False
        if operator == "lt":
            try:
                if float(actual) >= float(expected):
                    return False
            except Exception:
                return False

    return True


async def _execute_action(action: Dict[str, Any], trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single automation action."""
    action_type = (action.get("type") or action.get("action") or "").lower()
    params = action.get("params") or action.get("data") or {}

    if action_type == "send_email":
        to_email = params.get("to") or trigger_data.get("email")
        subject = params.get("subject") or "Notification"
        html = params.get("html") or params.get("body") or ""
        text_content = params.get("text") or ""
        if not to_email:
            raise RuntimeError("send_email action requires recipient email")
        success = await asyncio.to_thread(send_email_message, to_email, subject, html, text_content)
        return {"action": "send_email", "success": bool(success), "to": to_email}

    if action_type == "send_sms":
        to_phone = params.get("to") or trigger_data.get("phone")
        message = params.get("message") or params.get("body") or ""
        if not to_phone:
            raise RuntimeError("send_sms action requires recipient phone")
        success = await send_sms_message(to_phone, message)
        return {"action": "send_sms", "success": bool(success), "to": to_phone}

    if action_type == "webhook":
        url = params.get("url")
        payload = params.get("payload") or trigger_data
        if not url:
            raise RuntimeError("webhook action requires url")
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(url, json=payload)
        return {"action": "webhook", "success": resp.status_code < 300, "status_code": resp.status_code}

    if action_type == "agent_task":
        from core.agent_execution_manager import AgentExecutionManager
        agent_name = params.get("agent_name") or params.get("agent")
        task = params.get("task") or "automation_action"
        if not agent_name:
            raise RuntimeError("agent_task action requires agent_name")
        manager = AgentExecutionManager()
        result = await manager.execute_agent(agent_name, task, {"trigger_data": trigger_data, "params": params})
        return {"action": "agent_task", "success": result.get("status") == "completed", "result": result}

    raise RuntimeError(f"Unsupported automation action: {action_type}")


# Models
class AutomationCreate(BaseModel):
    name: str
    trigger_type: str  # form_submission, page_visit, email_open, date_based, score_based
    trigger_config: Dict[str, Any]
    actions: List[Dict[str, Any]]
    conditions: Optional[List[Dict[str, Any]]] = []
    is_active: bool = True

# Endpoints
@router.post("/automations", response_model=dict)
async def create_automation(
    automation: AutomationCreate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create marketing automation workflow"""
    tenant_id = current_user.get("tenant_id")
    has_tenant = await _has_tenant_column(conn)
    if has_tenant and not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    if has_tenant:
        query = """
            INSERT INTO marketing_automations (
                tenant_id, name, trigger_type, trigger_config, actions,
                conditions, is_active
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        """
        params = [
            tenant_id,
            automation.name,
            automation.trigger_type,
            json.dumps(automation.trigger_config),
            json.dumps(automation.actions),
            json.dumps(automation.conditions),
            automation.is_active
        ]
    else:
        query = """
            INSERT INTO marketing_automations (
                name, trigger_type, trigger_config, actions,
                conditions, is_active
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """
        params = [
            automation.name,
            automation.trigger_type,
            json.dumps(automation.trigger_config),
            json.dumps(automation.actions),
            json.dumps(automation.conditions),
            automation.is_active
        ]

    result = await conn.fetchrow(query, *params)

    return {**dict(result), "id": str(result['id'])}

@router.post("/automations/{automation_id}/trigger")
async def trigger_automation(
    automation_id: str,
    trigger_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Manually trigger an automation"""
    tenant_id = current_user.get("tenant_id")
    has_tenant = await _has_tenant_column(conn)
    if has_tenant and not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    if has_tenant:
        query = "SELECT * FROM marketing_automations WHERE id = $1 AND tenant_id = $2 AND is_active = true"
        automation = await conn.fetchrow(query, uuid.UUID(automation_id), tenant_id)
    else:
        query = "SELECT * FROM marketing_automations WHERE id = $1 AND is_active = true"
        automation = await conn.fetchrow(query, uuid.UUID(automation_id))

    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found or inactive")

    # Execute automation in background
    background_tasks.add_task(
        execute_automation,
        automation_id,
        trigger_data
    )

    return {"status": "triggered", "automation_id": automation_id}

async def execute_automation(automation_id: str, trigger_data: dict):
    """Execute automation workflow"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is required for automation execution")

    conn = await asyncpg.connect(db_url)
    execution_id = str(uuid.uuid4())

    try:
        automation_row = await conn.fetchrow(
            "SELECT * FROM marketing_automations WHERE id = $1",
            uuid.UUID(automation_id)
        )

        if not automation_row:
            raise RuntimeError("Automation not found")

        automation = dict(automation_row)
        actions = _normalize_json(automation.get("actions"), [])
        conditions = _normalize_json(automation.get("conditions"), [])

        if not _evaluate_conditions(conditions, trigger_data):
            await conn.execute(
                """
                INSERT INTO automation_logs (automation_id, automation_name, trigger_data, status, error_message)
                VALUES ($1, $2, $3, 'skipped', 'Conditions not met')
                """,
                uuid.UUID(automation_id),
                automation.get("name"),
                json.dumps(trigger_data),
            )
            await conn.execute(
                """
                INSERT INTO automation_events (event_type, entity_type, entity_id, data, automation_id, payload)
                VALUES ('automation_skipped', 'marketing_automation', $1, $2, $3, $2)
                """,
                uuid.UUID(automation_id),
                json.dumps(trigger_data),
                uuid.UUID(automation_id),
            )
            return

        await conn.execute(
            """
            INSERT INTO automation_executions (id, automation_id, trigger_data, status, started_at)
            VALUES ($1, $2, $3, 'running', NOW())
            """,
            uuid.UUID(execution_id),
            uuid.UUID(automation_id),
            json.dumps(trigger_data),
        )

        results = []
        errors: list[str] = []
        for action in actions:
            try:
                result = await _execute_action(action, trigger_data)
                results.append(result)
                if not result.get("success", True):
                    errors.append(f"Action failed: {result}")
            except Exception as exc:
                errors.append(str(exc))
                results.append({"action": action.get("type") or action.get("action"), "success": False, "error": str(exc)})

        status = "completed" if not errors else "failed"
        await conn.execute(
            """
            UPDATE automation_executions
            SET status = $1, completed_at = NOW(), error_message = $2
            WHERE id = $3
            """,
            status,
            "; ".join(errors) if errors else None,
            uuid.UUID(execution_id),
        )

        await conn.execute(
            """
            INSERT INTO automation_logs (automation_id, automation_name, trigger_data, status, error_message)
            VALUES ($1, $2, $3, $4, $5)
            """,
            uuid.UUID(automation_id),
            automation.get("name"),
            json.dumps(trigger_data),
            status,
            "; ".join(errors) if errors else None,
        )

        await conn.execute(
            """
            INSERT INTO automation_events (event_type, entity_type, entity_id, data, automation_id, payload)
            VALUES ($1, 'marketing_automation', $2, $3, $2, $3)
            """,
            "automation_completed" if status == "completed" else "automation_failed",
            uuid.UUID(automation_id),
            json.dumps({"trigger_data": trigger_data, "results": results}),
        )
    finally:
        await conn.close()
    
@router.get("/automations/performance", response_model=dict)
async def get_automation_performance(
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get automation performance metrics"""
    tenant_id = current_user.get("tenant_id")
    has_tenant = await _has_tenant_column(conn)
    if has_tenant and not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    base_filter = ""
    params: list[Any] = []
    if has_tenant:
        base_filter = "WHERE tenant_id = $1"
        params.append(tenant_id)

    total_automations = await conn.fetchval(
        f"SELECT COUNT(*) FROM marketing_automations {base_filter}",
        *params
    )
    active_automations = await conn.fetchval(
        f"SELECT COUNT(*) FROM marketing_automations {base_filter} AND is_active = true"
        if base_filter else "SELECT COUNT(*) FROM marketing_automations WHERE is_active = true",
        *params
    )

    exec_params = params.copy()
    exec_filter = ""
    if has_tenant:
        exec_filter = "WHERE m.tenant_id = $1"

    total_executions = await conn.fetchval(
        f"""
        SELECT COUNT(*)
        FROM automation_executions e
        JOIN marketing_automations m ON e.automation_id = m.id
        {exec_filter}
        """,
        *exec_params
    )

    success_rate = await conn.fetchval(
        f"""
        SELECT AVG(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END) * 100
        FROM automation_executions e
        JOIN marketing_automations m ON e.automation_id = m.id
        {exec_filter}
        """,
        *exec_params
    )

    completion_filter = exec_filter if exec_filter else "WHERE 1=1"
    avg_completion = await conn.fetchval(
        f"""
        SELECT AVG(EXTRACT(EPOCH FROM (e.completed_at - e.started_at)) / 60)
        FROM automation_executions e
        JOIN marketing_automations m ON e.automation_id = m.id
        {completion_filter} AND e.completed_at IS NOT NULL
        """,
        *exec_params
    )

    top_rows = await conn.fetch(
        f"""
        SELECT m.name,
               COUNT(*) AS executions,
               AVG(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END) * 100 AS success_rate
        FROM automation_executions e
        JOIN marketing_automations m ON e.automation_id = m.id
        {exec_filter}
        GROUP BY m.name
        ORDER BY executions DESC
        LIMIT 5
        """,
        *exec_params
    )

    top_performers = [
        {"name": row["name"], "executions": row["executions"], "conversion": row["success_rate"] or 0}
        for row in top_rows
    ]

    return {
        "total_automations": total_automations or 0,
        "active_automations": active_automations or 0,
        "total_executions": total_executions or 0,
        "success_rate": success_rate or 0,
        "average_completion_time": avg_completion,
        "top_performers": top_performers
    }
