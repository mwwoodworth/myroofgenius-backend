"""
Job Scheduling System
Manage job scheduling, crew assignments, and calendar integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import logging
import json
from uuid import uuid4

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from services.audit_service import log_data_access, log_data_modification

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/jobs/schedule", tags=["Job Scheduling"])

# ============================================================================
# MODELS
# ============================================================================

class ScheduleSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    crew_id: Optional[str] = None
    employee_ids: Optional[List[str]] = []
    notes: Optional[str] = None

class ScheduleConflict(BaseModel):
    job_id: str
    job_title: str
    conflict_type: str  # overlap, resource, travel_time
    start_time: datetime
    end_time: datetime
    details: str

class ResourceAvailability(BaseModel):
    resource_id: str
    resource_type: str  # crew, employee, equipment
    resource_name: str
    available: bool
    conflicts: List[ScheduleConflict] = []

class ScheduleOptimizationRequest(BaseModel):
    job_ids: List[str]
    start_date: date
    end_date: date
    optimize_for: str = "efficiency"  # efficiency, travel, balance
    constraints: Optional[Dict[str, Any]] = {}

# ============================================================================
# SCHEDULING ENDPOINTS
# ============================================================================

@router.get("/calendar")
async def get_schedule_calendar(
    start_date: date = Query(...),
    end_date: date = Query(...),
    crew_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    include_completed: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get scheduled jobs in calendar format"""
    try:
        # Build query
        query = """
            SELECT 
                j.id,
                j.title,
                j.customer_id,
                c.name as customer_name,
                j.status,
                j.priority,
                j.scheduled_start,
                j.scheduled_end,
                j.service_address,
                j.service_city,
                j.service_state,
                j.assigned_crew_id,
                cr.name as crew_name,
                j.estimated_hours,
                j.job_type,
                ARRAY_AGG(DISTINCT e.id) as assigned_employee_ids,
                ARRAY_AGG(DISTINCT e.first_name || ' ' || e.last_name) as assigned_employees
            FROM jobs j
            LEFT JOIN customers c ON j.customer_id = c.id
            LEFT JOIN crews cr ON j.assigned_crew_id = cr.id
            LEFT JOIN employee_jobs ej ON j.id = ej.job_id
            LEFT JOIN employees e ON ej.employee_id = e.id
            WHERE j.scheduled_start >= :start_date
            AND j.scheduled_start <= :end_date
        """
        
        params = {
            "start_date": start_date,
            "end_date": end_date + timedelta(days=1)  # Include end date
        }
        
        if not include_completed:
            query += " AND j.status NOT IN ('completed', 'cancelled', 'invoiced')"
        
        if crew_id:
            query += " AND j.assigned_crew_id = :crew_id"
            params["crew_id"] = crew_id
        
        if employee_id:
            query += " AND EXISTS (SELECT 1 FROM employee_jobs WHERE job_id = j.id AND employee_id = :employee_id)"
            params["employee_id"] = employee_id
        
        query += " GROUP BY j.id, c.name, cr.name ORDER BY j.scheduled_start"
        
        result = db.execute(text(query), params)
        
        # Format as calendar events
        events = []
        for row in result:
            event = dict(row._mapping)
            event["id"] = str(event["id"])
            event["customer_id"] = str(event["customer_id"])
            if event["assigned_crew_id"]:
                event["assigned_crew_id"] = str(event["assigned_crew_id"])
            
            # Format as calendar event
            calendar_event = {
                "id": event["id"],
                "title": f"{event['title']} - {event['customer_name']}",
                "start": event["scheduled_start"].isoformat() if event["scheduled_start"] else None,
                "end": event["scheduled_end"].isoformat() if event["scheduled_end"] else None,
                "allDay": False,
                "color": _get_event_color(event["status"], event["priority"]),
                "extendedProps": {
                    "status": event["status"],
                    "priority": event["priority"],
                    "job_type": event["job_type"],
                    "crew": event["crew_name"],
                    "employees": event["assigned_employees"],
                    "address": f"{event['service_address']}, {event['service_city']}, {event['service_state']}",
                    "estimated_hours": event["estimated_hours"]
                }
            }
            events.append(calendar_event)
        
        log_data_access(db, current_user["id"], "jobs", "schedule_calendar", len(events))
        
        return {
            "events": events,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total": len(events)
        }
    
    except Exception as e:
        logger.error(f"Error fetching schedule calendar: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch schedule")

@router.post("/{job_id}/schedule")
async def schedule_job(
    job_id: str,
    schedule: ScheduleSlot,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule or reschedule a job"""
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
        
        # Check for conflicts
        conflicts = await check_schedule_conflicts(
            job_id, schedule.start_time, schedule.end_time,
            schedule.crew_id, schedule.employee_ids, db
        )
        
        if conflicts:
            return {
                "success": False,
                "message": "Schedule conflicts detected",
                "conflicts": conflicts
            }
        
        # Update job schedule
        db.execute(
            text("""
                UPDATE jobs
                SET scheduled_start = :start_time,
                    scheduled_end = :end_time,
                    assigned_crew_id = :crew_id,
                    status = CASE 
                        WHEN status = 'draft' THEN 'scheduled'
                        ELSE status
                    END,
                    updated_at = NOW()
                WHERE id = :id
            """),
            {
                "id": job_id,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "crew_id": schedule.crew_id
            }
        )
        
        # Update employee assignments
        if schedule.employee_ids:
            # Remove existing assignments
            db.execute(
                text("DELETE FROM employee_jobs WHERE job_id = :job_id"),
                {"job_id": job_id}
            )
            
            # Add new assignments
            for employee_id in schedule.employee_ids:
                db.execute(
                    text("""
                        INSERT INTO employee_jobs (id, employee_id, job_id, assigned_at)
                        VALUES (:id, :employee_id, :job_id, NOW())
                    """),
                    {
                        "id": str(uuid4()),
                        "employee_id": employee_id,
                        "job_id": job_id
                    }
                )
        
        # Add to status history
        db.execute(
            text("""
                INSERT INTO job_status_history (
                    id, job_id, from_status, to_status,
                    changed_by, changed_at, reason
                )
                VALUES (
                    :id, :job_id, :from_status, :to_status,
                    :user_id, NOW(), 'Job scheduled'
                )
            """),
            {
                "id": str(uuid4()),
                "job_id": job_id,
                "from_status": job.status,
                "to_status": "scheduled" if job.status == "draft" else job.status,
                "user_id": current_user["id"]
            }
        )
        
        db.commit()
        
        log_data_modification(
            db, current_user["id"], "jobs", "schedule",
            job_id, new_values=schedule.dict()
        )
        
        return {
            "success": True,
            "message": "Job scheduled successfully",
            "schedule": {
                "start": schedule.start_time.isoformat(),
                "end": schedule.end_time.isoformat(),
                "crew_id": schedule.crew_id,
                "employee_ids": schedule.employee_ids
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error scheduling job: {e}")
        raise HTTPException(status_code=500, detail="Failed to schedule job")

@router.get("/{job_id}/availability")
async def check_resource_availability(
    job_id: str,
    proposed_start: datetime = Query(...),
    proposed_end: datetime = Query(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check resource availability for a job"""
    try:
        # Get job requirements
        job = db.execute(
            text("""
                SELECT j.*, jt.required_crew_size, jt.required_skills
                FROM jobs j
                LEFT JOIN job_types jt ON j.job_type = jt.type_code
                WHERE j.id = :id
            """),
            {"id": job_id}
        ).fetchone()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        availability = []
        
        # Check crew availability
        crews = db.execute(
            text("""
                SELECT id, name
                FROM crews
                WHERE status = 'active'
            """)
        ).fetchall()
        
        for crew in crews:
            crew_conflicts = await check_crew_conflicts(
                str(crew.id), proposed_start, proposed_end, db
            )
            
            availability.append(ResourceAvailability(
                resource_id=str(crew.id),
                resource_type="crew",
                resource_name=crew.name,
                available=len(crew_conflicts) == 0,
                conflicts=crew_conflicts
            ))
        
        # Check employee availability
        employees = db.execute(
            text("""
                SELECT id, first_name, last_name
                FROM employees
                WHERE status = 'active'
            """)
        ).fetchall()
        
        for employee in employees:
            emp_conflicts = await check_employee_conflicts(
                str(employee.id), proposed_start, proposed_end, db
            )
            
            availability.append(ResourceAvailability(
                resource_id=str(employee.id),
                resource_type="employee",
                resource_name=f"{employee.first_name} {employee.last_name}",
                available=len(emp_conflicts) == 0,
                conflicts=emp_conflicts
            ))
        
        return {
            "job_id": job_id,
            "proposed_start": proposed_start.isoformat(),
            "proposed_end": proposed_end.isoformat(),
            "availability": availability,
            "available_crews": len([r for r in availability if r.resource_type == "crew" and r.available]),
            "available_employees": len([r for r in availability if r.resource_type == "employee" and r.available])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        raise HTTPException(status_code=500, detail="Failed to check availability")

@router.post("/optimize")
async def optimize_schedule(
    request: ScheduleOptimizationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Optimize job scheduling for efficiency"""
    try:
        # Get jobs to optimize
        jobs = db.execute(
            text("""
                SELECT j.*, c.service_latitude, c.service_longitude,
                       jt.average_duration_hours
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id = c.id
                LEFT JOIN job_types jt ON j.job_type = jt.type_code
                WHERE j.id = ANY(:job_ids)
                AND j.status IN ('draft', 'scheduled')
            """),
            {"job_ids": request.job_ids}
        ).fetchall()
        
        if not jobs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No eligible jobs found for optimization"
            )
        
        # Simple optimization algorithm
        optimized_schedule = []
        current_date = datetime.combine(request.start_date, datetime.min.time())
        
        # Group jobs by location proximity (simplified)
        job_list = list(jobs)
        
        if request.optimize_for == "travel":
            # Sort by location (simplified - in production, use proper routing)
            job_list.sort(key=lambda j: (j.service_latitude or 0, j.service_longitude or 0))
        elif request.optimize_for == "balance":
            # Distribute evenly across days
            pass
        else:  # efficiency
            # Pack jobs tightly
            job_list.sort(key=lambda j: j.estimated_hours or j.average_duration_hours or 2)
        
        for job in job_list:
            duration_hours = job.estimated_hours or job.average_duration_hours or 2
            
            # Find next available slot
            while current_date.weekday() in [5, 6]:  # Skip weekends
                current_date += timedelta(days=1)
            
            if current_date.date() > request.end_date:
                break
            
            start_time = current_date.replace(hour=8)  # Start at 8 AM
            end_time = start_time + timedelta(hours=duration_hours)
            
            # Check if we exceed working hours
            if end_time.hour > 17:  # After 5 PM
                current_date += timedelta(days=1)
                continue
            
            optimized_schedule.append({
                "job_id": str(job.id),
                "job_title": job.title,
                "proposed_start": start_time.isoformat(),
                "proposed_end": end_time.isoformat(),
                "duration_hours": duration_hours
            })
            
            # Move to next slot
            current_date = end_time
            if end_time.hour >= 16:  # Late in the day, move to next day
                current_date = (current_date + timedelta(days=1)).replace(hour=8, minute=0)
        
        return {
            "optimization_type": request.optimize_for,
            "jobs_optimized": len(optimized_schedule),
            "schedule": optimized_schedule,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize schedule")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def check_schedule_conflicts(
    job_id: str,
    start_time: datetime,
    end_time: datetime,
    crew_id: Optional[str],
    employee_ids: List[str],
    db: Session
) -> List[ScheduleConflict]:
    """Check for scheduling conflicts"""
    conflicts = []
    
    # Check crew conflicts
    if crew_id:
        crew_conflicts = await check_crew_conflicts(crew_id, start_time, end_time, db, job_id)
        conflicts.extend(crew_conflicts)
    
    # Check employee conflicts
    for employee_id in employee_ids:
        emp_conflicts = await check_employee_conflicts(employee_id, start_time, end_time, db, job_id)
        conflicts.extend(emp_conflicts)
    
    return conflicts

async def check_crew_conflicts(
    crew_id: str,
    start_time: datetime,
    end_time: datetime,
    db: Session,
    exclude_job_id: Optional[str] = None
) -> List[ScheduleConflict]:
    """Check if crew has conflicts"""
    query = """
        SELECT id, title, scheduled_start, scheduled_end
        FROM jobs
        WHERE assigned_crew_id = :crew_id
        AND status NOT IN ('completed', 'cancelled', 'invoiced')
        AND scheduled_start < :end_time
        AND scheduled_end > :start_time
    """
    
    params = {
        "crew_id": crew_id,
        "start_time": start_time,
        "end_time": end_time
    }
    
    if exclude_job_id:
        query += " AND id != :exclude_id"
        params["exclude_id"] = exclude_job_id
    
    result = db.execute(text(query), params)
    
    conflicts = []
    for row in result:
        conflicts.append(ScheduleConflict(
            job_id=str(row.id),
            job_title=row.title,
            conflict_type="overlap",
            start_time=row.scheduled_start,
            end_time=row.scheduled_end,
            details=f"Crew already scheduled for {row.title}"
        ))
    
    return conflicts

async def check_employee_conflicts(
    employee_id: str,
    start_time: datetime,
    end_time: datetime,
    db: Session,
    exclude_job_id: Optional[str] = None
) -> List[ScheduleConflict]:
    """Check if employee has conflicts"""
    query = """
        SELECT j.id, j.title, j.scheduled_start, j.scheduled_end
        FROM jobs j
        JOIN employee_jobs ej ON j.id = ej.job_id
        WHERE ej.employee_id = :employee_id
        AND j.status NOT IN ('completed', 'cancelled', 'invoiced')
        AND j.scheduled_start < :end_time
        AND j.scheduled_end > :start_time
    """
    
    params = {
        "employee_id": employee_id,
        "start_time": start_time,
        "end_time": end_time
    }
    
    if exclude_job_id:
        query += " AND j.id != :exclude_id"
        params["exclude_id"] = exclude_job_id
    
    result = db.execute(text(query), params)
    
    conflicts = []
    for row in result:
        conflicts.append(ScheduleConflict(
            job_id=str(row.id),
            job_title=row.title,
            conflict_type="overlap",
            start_time=row.scheduled_start,
            end_time=row.scheduled_end,
            details=f"Employee already scheduled for {row.title}"
        ))
    
    return conflicts

def _get_event_color(status: str, priority: str) -> str:
    """Get calendar event color based on status and priority"""
    if status == "completed":
        return "#28a745"  # Green
    elif status == "cancelled":
        return "#6c757d"  # Gray
    elif priority == "emergency":
        return "#dc3545"  # Red
    elif priority == "urgent":
        return "#fd7e14"  # Orange
    elif priority == "high":
        return "#ffc107"  # Yellow
    elif status == "in_progress":
        return "#17a2b8"  # Cyan
    else:
        return "#007bff RETURNING *"  # Blue
