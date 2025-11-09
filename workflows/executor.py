import asyncpg
from .state_manager import WorkflowStateManager
import logging

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.state_manager = WorkflowStateManager(db_pool)

    async def run(self, workflow_name: str, initial_state: dict, workflow_instance: object, max_retries: int = 3):
        # Get workflow and steps from database
        async with self.db_pool.acquire() as conn:
            workflow = await conn.fetchrow("SELECT * FROM workflows WHERE name = $1", workflow_name)
            if not workflow:
                raise ValueError(f"Workflow '{workflow_name}' not found")

            steps = await conn.fetch("SELECT * FROM workflow_steps WHERE workflow_id = $1 ORDER BY step_order", workflow['id'])

        # Execute steps
        state = initial_state
        for step in steps:
            function_name = step['function_name']
            if hasattr(workflow_instance, function_name):
                method = getattr(workflow_instance, function_name)
                
                for attempt in range(max_retries):
                    try:
                        state = await method(state)
                        break  # Success, move to next step
                    except Exception as e:
                        logger.error(f"Error executing step '{step['name']}' (attempt {attempt + 1}/{max_retries}): {e}")
                        state["errors"].append(f"Error in step '{step['name']}': {e}")
                        if attempt + 1 == max_retries:
                            raise  # Re-raise the exception to fail the workflow
            else:
                raise AttributeError(f"Workflow instance is missing method '{function_name}'")
        
        return state
