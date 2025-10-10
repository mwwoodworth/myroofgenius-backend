"""
Workflow State Management
Handles persistence of workflow state to database
"""
from typing import Dict, Any, Optional
from datetime import datetime
import asyncpg
import json

class WorkflowStateManager:
    """Manages workflow state persistence to Supabase"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def save_state(
        self,
        workflow_id: str,
        workflow_type: str,
        state: Dict[str, Any],
        user_id: Optional[str] = None,
        status: str = "running"
    ) -> None:
        """Save or update workflow state"""

        # Convert complex objects to JSON-serializable format
        safe_state = self._make_json_safe(state)

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO workflow_states (id, workflow_type, state, user_id, status, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO UPDATE SET
                    state = $3,
                    status = $5,
                    updated_at = $6
            """, workflow_id, workflow_type, json.dumps(safe_state), user_id, status, datetime.now())

    async def load_state(self, workflow_id: str) -> Dict[str, Any]:
        """Load workflow state by ID"""

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT state FROM workflow_states WHERE id = $1
            """, workflow_id)

            if not row:
                raise ValueError(f"Workflow not found: {workflow_id}")

            return json.loads(row["state"])

    async def log_step(
        self,
        workflow_id: str,
        step_name: str,
        step_result: Dict[str, Any],
        duration_ms: int
    ) -> None:
        """Log individual workflow step execution"""

        safe_result = self._make_json_safe(step_result)

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO workflow_history (workflow_id, step_name, step_result, duration_ms)
                VALUES ($1, $2, $3, $4)
            """, workflow_id, step_name, json.dumps(safe_result), duration_ms)

    async def log_agent_call(
        self,
        workflow_id: str,
        agent_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        duration_ms: int,
        success: bool
    ) -> None:
        """Log AI agent calls for analytics"""

        safe_input = self._make_json_safe(input_data)
        safe_output = self._make_json_safe(output_data)

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO agent_calls (workflow_id, agent_name, input, output, duration_ms, success)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, workflow_id, agent_name, json.dumps(safe_input), json.dumps(safe_output), duration_ms, success)

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution status and results"""

        async with self.db_pool.acquire() as conn:
            # Get workflow state
            workflow_row = await conn.fetchrow("""
                SELECT workflow_type, state, status, created_at, updated_at
                FROM workflow_states
                WHERE id = $1
            """, workflow_id)

            if not workflow_row:
                raise ValueError(f"Workflow not found: {workflow_id}")

            # Get execution history
            history_rows = await conn.fetch("""
                SELECT step_name, step_result, duration_ms, created_at
                FROM workflow_history
                WHERE workflow_id = $1
                ORDER BY created_at ASC
            """, workflow_id)

            # Get agent calls
            agent_rows = await conn.fetch("""
                SELECT agent_name, success, duration_ms
                FROM agent_calls
                WHERE workflow_id = $1
                ORDER BY created_at ASC
            """, workflow_id)

            return {
                "workflow_id": workflow_id,
                "workflow_type": workflow_row["workflow_type"],
                "status": workflow_row["status"],
                "state": json.loads(workflow_row["state"]),
                "created_at": workflow_row["created_at"].isoformat(),
                "updated_at": workflow_row["updated_at"].isoformat(),
                "steps": [
                    {
                        "name": row["step_name"],
                        "result": json.loads(row["step_result"]) if row["step_result"] else {},
                        "duration_ms": row["duration_ms"],
                        "timestamp": row["created_at"].isoformat()
                    }
                    for row in history_rows
                ],
                "agent_calls": [
                    {
                        "agent": row["agent_name"],
                        "success": row["success"],
                        "duration_ms": row["duration_ms"]
                    }
                    for row in agent_rows
                ]
            }

    def _make_json_safe(self, obj: Any) -> Any:
        """Convert complex objects to JSON-serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_safe(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # Convert non-serializable objects to string
            return str(obj)
