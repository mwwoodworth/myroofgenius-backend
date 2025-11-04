"""
Task 109: R&D Management
Research and development project management
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4
import asyncpg
import json
import asyncio
from decimal import Decimal

router = APIRouter()

# Database connection
async def get_db():
    conn = await asyncpg.connect(
        host="aws-0-us-east-2.pooler.supabase.com",
        port=5432,
        user="postgres.yomagoqdmxszqtdwuhab",
        password="Brain0ps2O2S",
        database="postgres"
    )
    try:
        yield conn
    finally:
        await conn.close()

@router.get("/projects")
async def list_rd_projects(
    status: Optional[str] = None,
    stage: Optional[str] = None,
    db=Depends(get_db)
):
    """List R&D projects"""
    query = """
        SELECT id, project_code, project_name, research_area,
               stage, status, budget, start_date, estimated_completion
        FROM rd_projects
        WHERE ($1::text IS NULL OR status = $1)
        AND ($2::text IS NULL OR stage = $2)
        ORDER BY created_at DESC
    """
    rows = await db.fetch(query, status, stage)
    if not rows:
        return []
    return [dict(row) for row in rows]

@router.post("/projects")
async def create_rd_project(
    project: Dict[str, Any],
    db=Depends(get_db)
):
    """Create R&D project"""
    project_id = str(uuid4())
    project_code = f"RD-{datetime.now().strftime('%Y')}-{project_id[:6]}"

    query = """
        INSERT INTO rd_projects (id, project_code, project_name,
                                research_area, objectives, budget,
                                team_members, status, stage)
        VALUES ($1, $2, $3, $4, $5, $6, $7, 'active', 'research')
        RETURNING id, project_code
    """

    result = await db.fetchrow(
        query, project_id, project_code, project['project_name'],
        project.get('research_area', 'general'),
        json.dumps(project.get('objectives', [])),
        project.get('budget', 0),
        json.dumps(project.get('team_members', []))
    )

    return dict(result)

@router.post("/experiments")
async def log_experiment(
    experiment: Dict[str, Any],
    db=Depends(get_db)
):
    """Log R&D experiment"""
    exp_id = str(uuid4())

    query = """
        INSERT INTO rd_experiments (id, project_id, experiment_name,
                                   hypothesis, methodology, results,
                                   conclusion, date_conducted)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
    """

    await db.execute(
        query, exp_id, experiment['project_id'], experiment['experiment_name'],
        experiment.get('hypothesis'), json.dumps(experiment.get('methodology', {})),
        json.dumps(experiment.get('results', {})), experiment.get('conclusion'),
        experiment.get('date_conducted', date.today())
    )

    return {"experiment_id": exp_id, "status": "logged"}

@router.get("/innovations")
async def get_innovation_pipeline(db=Depends(get_db)):
    """Get innovation pipeline"""
    query = """
        SELECT
            stage,
            COUNT(*) as project_count,
            SUM(budget) as total_budget,
            AVG(EXTRACT(DAY FROM CURRENT_DATE - start_date)) as avg_days_in_stage
        FROM rd_projects
        WHERE status = 'active'
        GROUP BY stage
        ORDER BY
            CASE stage
                WHEN 'research' THEN 1
                WHEN 'development' THEN 2
                WHEN 'testing' THEN 3
                WHEN 'pilot' THEN 4
                WHEN 'commercialization' THEN 5
                ELSE 6
            END
    """
    rows = await db.fetch(query)
    if not rows:
        return []

    return {
        "pipeline": [dict(row) for row in rows],
        "total_projects": sum(row['project_count'] for row in rows),
        "total_investment": sum(float(row['total_budget'] or 0) for row in rows),
        "avg_time_to_market": 365  # Would calculate from historical data
    }
