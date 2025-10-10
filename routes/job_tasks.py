"""
Job Task Management
Manage job tasks, checklists, and work breakdown structures
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
from uuid import uuid4

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from services.audit_service import log_data_modification, log_data_access

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/jobs", tags=["Job Tasks"])

# ============================================================================
# ENUMS AND MODELS
# ============================================================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskCategory(str, Enum):
    PREPARATION = "preparation"
    INSTALLATION = "installation"
    INSPECTION = "inspection"
    CLEANUP = "cleanup"
    DOCUMENTATION = "documentation"
    SAFETY = "safety"
    QUALITY = "quality"
    OTHER = "other"

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: TaskCategory
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_hours: Optional[float] = Field(None, ge=0)
    assigned_to: Optional[str] = None
    parent_task_id: Optional[str] = None
    dependencies: Optional[List[str]] = []
    checklist_items: Optional[List[str]] = []
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = []
    custom_fields: Optional[Dict[str, Any]] = {}

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[TaskCategory] = None
    priority: Optional[TaskPriority] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

class TaskStatusUpdate(BaseModel):
    status: TaskStatus
    notes: Optional[str] = None
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)

class ChecklistItemUpdate(BaseModel):
    item_id: str
    completed: bool
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

class TaskTemplate(BaseModel):
    name: str
    description: Optional[str] = None
    job_type: str
    tasks: List[TaskCreate]
    estimated_total_hours: Optional[float] = None
    is_active: bool = True

# ============================================================================
# TASK MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/{job_id}/tasks", status_code=status.HTTP_201_CREATED)
async def create_job_task(
    job_id: str,
    task: TaskCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new task for a job"""
    try:
        # Verify job exists
        job = db.execute(
            text("SELECT id, status FROM jobs WHERE id = :id"),
            {"id": job_id}
        ).fetchone()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        task_id = str(uuid4())
        
        # Create task
        db.execute(
            text("""
                INSERT INTO job_tasks (
                    id, job_id, title, description,
                    category, priority, status,
                    estimated_hours, assigned_to,
                    parent_task_id, dependencies,
                    due_date, tags, custom_fields,
                    created_at, created_by, updated_at
                )
                VALUES (
                    :id, :job_id, :title, :description,
                    :category, :priority, :status,
                    :estimated_hours, :assigned_to,
                    :parent_task_id, :dependencies::jsonb,
                    :due_date, :tags::jsonb, :custom_fields::jsonb,
                    NOW(), :created_by, NOW()
                )
            """),
            {
                "id": task_id,
                "job_id": job_id,
                "title": task.title,
                "description": task.description,
                "category": task.category,
                "priority": task.priority,
                "status": TaskStatus.PENDING,
                "estimated_hours": task.estimated_hours,
                "assigned_to": task.assigned_to,
                "parent_task_id": task.parent_task_id,
                "dependencies": json.dumps(task.dependencies or []),
                "due_date": task.due_date,
                "tags": json.dumps(task.tags or []),
                "custom_fields": json.dumps(task.custom_fields or {}),
                "created_by": current_user["id"]
            }
        )
        
        # Create checklist items if provided
        if task.checklist_items:
            for item_text in task.checklist_items:
                db.execute(
                    text("""
                        INSERT INTO task_checklist_items (
                            id, task_id, item_text, is_completed,
                            created_at, display_order
                        )
                        VALUES (
                            :id, :task_id, :item_text, FALSE,
                            NOW(), :order
                        )
                    """),
                    {
                        "id": str(uuid4()),
                        "task_id": task_id,
                        "item_text": item_text,
                        "order": task.checklist_items.index(item_text)
                    }
                )
        
        # Create notification if task is assigned
        if task.assigned_to:
            db.execute(
                text("""
                    INSERT INTO notifications (
                        id, user_id, type, title, message,
                        resource_type, resource_id, created_at
                    )
                    VALUES (
                        :id, :user_id, 'task_assigned',
                        'New Task Assigned', :message,
                        'task', :task_id, NOW()
                    )
                """),
                {
                    "id": str(uuid4()),
                    "user_id": task.assigned_to,
                    "message": f"You have been assigned task: {task.title}",
                    "task_id": task_id
                }
            )
        
        db.commit()
        
        log_data_modification(
            db, current_user["id"], "job_tasks", "create",
            task_id, new_values=task.dict()
        )
        
        return {
            "id": task_id,
            "message": "Task created successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")

@router.get("/{job_id}/tasks")
async def get_job_tasks(
    job_id: str,
    status: Optional[TaskStatus] = None,
    category: Optional[TaskCategory] = None,
    assigned_to: Optional[str] = None,
    include_subtasks: bool = Query(True),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tasks for a job"""
    try:
        # Build query
        query = """
            SELECT 
                t.*,
                u.name as assigned_to_name,
                COUNT(DISTINCT st.id) as subtask_count,
                COUNT(DISTINCT ci.id) as checklist_item_count,
                COUNT(DISTINCT CASE WHEN ci.is_completed THEN ci.id END) as completed_items,
                CASE 
                    WHEN COUNT(ci.id) > 0 THEN 
                        ROUND(100.0 * COUNT(CASE WHEN ci.is_completed THEN 1 END) / COUNT(ci.id), 0)
                    ELSE t.completion_percentage
                END as calculated_completion
            FROM job_tasks t
            LEFT JOIN users u ON t.assigned_to = u.id
            LEFT JOIN job_tasks st ON st.parent_task_id = t.id
            LEFT JOIN task_checklist_items ci ON ci.task_id = t.id
            WHERE t.job_id = :job_id
        """
        
        params = {"job_id": job_id}
        
        # Apply filters
        if not include_subtasks:
            query += " AND t.parent_task_id IS NULL"
        
        if status:
            query += " AND t.status = :status"
            params["status"] = status
        
        if category:
            query += " AND t.category = :category"
            params["category"] = category
        
        if assigned_to:
            query += " AND t.assigned_to = :assigned_to"
            params["assigned_to"] = assigned_to
        
        query += " GROUP BY t.id, u.name ORDER BY t.priority DESC, t.created_at"
        
        result = db.execute(text(query), params)
        
        tasks = []
        for row in result:
            task = dict(row._mapping)
            task["id"] = str(task["id"])
            task["job_id"] = str(task["job_id"])
            if task["assigned_to"]:
                task["assigned_to"] = str(task["assigned_to"])
            if task["parent_task_id"]:
                task["parent_task_id"] = str(task["parent_task_id"])
            tasks.append(task)
        
        # Build task hierarchy if including subtasks
        if include_subtasks:
            task_map = {task["id"]: task for task in tasks}
            root_tasks = []
            
            for task in tasks:
                if task["parent_task_id"] and task["parent_task_id"] in task_map:
                    parent = task_map[task["parent_task_id"]]
                    if "subtasks" not in parent:
                        parent["subtasks"] = []
                    parent["subtasks"].append(task)
                elif not task["parent_task_id"]:
                    root_tasks.append(task)
            
            tasks = root_tasks
        
        log_data_access(db, current_user["id"], "job_tasks", "list", len(tasks))
        
        return {
            "job_id": job_id,
            "tasks": tasks,
            "total": len(tasks)
        }
    
    except Exception as e:
        logger.error(f"Error fetching job tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tasks")

@router.put("/{job_id}/tasks/{task_id}/status")
async def update_task_status(
    job_id: str,
    task_id: str,
    status_update: TaskStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update task status and completion"""
    try:
        # Verify task exists
        task = db.execute(
            text("SELECT * FROM job_tasks WHERE id = :id AND job_id = :job_id"),
            {"id": task_id, "job_id": job_id}
        ).fetchone()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        old_status = task.status
        
        # Check dependencies if moving to in_progress
        if status_update.status == TaskStatus.IN_PROGRESS:
            if task.dependencies:
                blocked_deps = db.execute(
                    text("""
                        SELECT id, title FROM job_tasks
                        WHERE id = ANY(:deps::uuid[])
                        AND status != 'completed'
                    """),
                    {"deps": task.dependencies}
                ).fetchall()
                
                if blocked_deps:
                    dep_titles = ", ".join([d.title for d in blocked_deps])
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot start task. Blocked by: {dep_titles}"
                    )
        
        # Update task status
        update_fields = {
            "status": status_update.status,
            "updated_at": "NOW()"
        }
        
        if status_update.completion_percentage is not None:
            update_fields["completion_percentage"] = status_update.completion_percentage
        
        if status_update.status == TaskStatus.IN_PROGRESS:
            update_fields["started_at"] = "NOW()"
        elif status_update.status == TaskStatus.COMPLETED:
            update_fields["completed_at"] = "NOW()"
            update_fields["completion_percentage"] = 100
        
        query = f"""
            UPDATE job_tasks
            SET {', '.join([f'{k} = :{k}' if ':' in str(v) else f'{k} = {v}' for k, v in update_fields.items()])}
            WHERE id = :id
        """
        
        params = {"id": task_id}
        for k, v in update_fields.items():
            if ':' in str(v):
                params[k] = v
        
        db.execute(text(query), params)
        
        # Add to task history
        db.execute(
            text("""
                INSERT INTO task_status_history (
                    id, task_id, from_status, to_status,
                    changed_by, changed_at, notes
                )
                VALUES (
                    :id, :task_id, :from_status, :to_status,
                    :user_id, NOW(), :notes
                )
            """),
            {
                "id": str(uuid4()),
                "task_id": task_id,
                "from_status": old_status,
                "to_status": status_update.status,
                "user_id": current_user["id"],
                "notes": status_update.notes
            }
        )
        
        # Update parent task if this is a subtask
        if task.parent_task_id:
            _update_parent_task_progress(task.parent_task_id, db)
        
        db.commit()
        
        log_data_modification(
            db, current_user["id"], "job_tasks", "status_update",
            task_id, old_values={"status": old_status},
            new_values={"status": status_update.status}
        )
        
        return {
            "message": "Task status updated successfully",
            "old_status": old_status,
            "new_status": status_update.status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating task status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task status")

@router.put("/{job_id}/tasks/{task_id}/checklist")
async def update_checklist_item(
    job_id: str,
    task_id: str,
    item_update: ChecklistItemUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update checklist item completion"""
    try:
        # Verify task exists
        task = db.execute(
            text("SELECT id FROM job_tasks WHERE id = :id AND job_id = :job_id"),
            {"id": task_id, "job_id": job_id}
        ).fetchone()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Update checklist item
        db.execute(
            text("""
                UPDATE task_checklist_items
                SET is_completed = :completed,
                    completed_by = :completed_by,
                    completed_at = :completed_at,
                    notes = :notes,
                    updated_at = NOW()
                WHERE id = :id AND task_id = :task_id
            """),
            {
                "id": item_update.item_id,
                "task_id": task_id,
                "completed": item_update.completed,
                "completed_by": item_update.completed_by or current_user["id"],
                "completed_at": item_update.completed_at or datetime.utcnow() if item_update.completed else None,
                "notes": item_update.notes
            }
        )
        
        # Update task completion percentage based on checklist
        result = db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_items,
                    COUNT(CASE WHEN is_completed THEN 1 END) as completed_items
                FROM task_checklist_items
                WHERE task_id = :task_id
            """),
            {"task_id": task_id}
        ).fetchone()
        
        if result and result.total_items > 0:
            completion = int(100 * result.completed_items / result.total_items)
            
            db.execute(
                text("""
                    UPDATE job_tasks
                    SET completion_percentage = :completion,
                        status = CASE
                            WHEN :completion = 100 THEN 'completed'
                            WHEN :completion > 0 THEN 'in_progress'
                            ELSE status
                        END,
                        updated_at = NOW()
                    WHERE id = :task_id
                """),
                {"task_id": task_id, "completion": completion}
            )
        
        db.commit()
        
        return {
            "message": "Checklist item updated successfully",
            "item_id": item_update.item_id,
            "completed": item_update.completed
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating checklist item: {e}")
        raise HTTPException(status_code=500, detail="Failed to update checklist")

@router.get("/templates")
async def get_task_templates(
    job_type: Optional[str] = None,
    is_active: bool = Query(True),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available task templates"""
    try:
        query = """
            SELECT * FROM task_templates
            WHERE is_active = :is_active
        """
        
        params = {"is_active": is_active}
        
        if job_type:
            query += " AND job_type = :job_type"
            params["job_type"] = job_type
        
        query += " ORDER BY name"
        
        result = db.execute(text(query), params)
        
        templates = []
        for row in result:
            template = dict(row._mapping)
            template["id"] = str(template["id"])
            templates.append(template)
        
        return {"templates": templates, "total": len(templates)}
    
    except Exception as e:
        logger.error(f"Error fetching task templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch templates")

@router.post("/{job_id}/tasks/from-template")
async def create_tasks_from_template(
    job_id: str,
    template_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create tasks from a template"""
    try:
        # Get template
        template = db.execute(
            text("SELECT * FROM task_templates WHERE id = :id AND is_active = TRUE"),
            {"id": template_id}
        ).fetchone()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Create tasks from template
        created_tasks = []
        task_id_map = {}  # Map template task IDs to new task IDs
        
        for template_task in template.tasks:
            task_id = str(uuid4())
            task_id_map[template_task.get("id")] = task_id
            
            # Map parent task ID if exists
            parent_id = None
            if template_task.get("parent_task_id") in task_id_map:
                parent_id = task_id_map[template_task["parent_task_id"]]
            
            db.execute(
                text("""
                    INSERT INTO job_tasks (
                        id, job_id, title, description,
                        category, priority, status,
                        estimated_hours, parent_task_id,
                        created_at, created_by
                    )
                    VALUES (
                        :id, :job_id, :title, :description,
                        :category, :priority, 'pending',
                        :estimated_hours, :parent_task_id,
                        NOW(), :created_by
                    )
                """),
                {
                    "id": task_id,
                    "job_id": job_id,
                    "title": template_task["title"],
                    "description": template_task.get("description"),
                    "category": template_task["category"],
                    "priority": template_task.get("priority", "medium"),
                    "estimated_hours": template_task.get("estimated_hours"),
                    "parent_task_id": parent_id,
                    "created_by": current_user["id"]
                }
            )
            
            created_tasks.append(task_id)
        
        db.commit()
        
        return {
            "message": "Tasks created from template successfully",
            "template_id": template_id,
            "tasks_created": len(created_tasks)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating tasks from template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create tasks from template")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _update_parent_task_progress(parent_task_id: str, db: Session):
    """Update parent task progress based on subtasks"""
    try:
        result = db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_subtasks,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_subtasks,
                    AVG(completion_percentage) as avg_completion
                FROM job_tasks
                WHERE parent_task_id = :parent_id
            """),
            {"parent_id": parent_task_id}
        ).fetchone()
        
        if result and result.total_subtasks > 0:
            completion = int(result.avg_completion or 0)
            
            # Update parent task
            db.execute(
                text("""
                    UPDATE job_tasks
                    SET completion_percentage = :completion,
                        status = CASE
                            WHEN :completion = 100 THEN 'completed'
                            WHEN :completion > 0 THEN 'in_progress'
                            ELSE status
                        END,
                        updated_at = NOW()
                    WHERE id = :parent_id
                """),
                {"parent_id": parent_task_id, "completion": completion}
            )
    
    except Exception as e:
        logger.error(f"Error updating parent task progress: {e} RETURNING * RETURNING *")
