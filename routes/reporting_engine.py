"""
Reporting Engine Module - Task 93
Advanced reporting and document generation
"""

from fastapi import APIRouter, HTTPException, Depends, Response, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json

router = APIRouter()

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

class ReportCreate(BaseModel):
    report_name: str
    report_type: str  # financial, operational, sales, custom
    parameters: Optional[Dict[str, Any]] = {}
    format: str = "pdf"  # pdf, excel, csv, html
    schedule: Optional[str] = None

@router.post("/reports")
async def create_report(
    report: ReportCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Generate report"""
    query = """
        INSERT INTO reports (
            report_name, report_type, parameters,
            format, status
        ) VALUES ($1, $2, $3, $4, $5)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        report.report_name,
        report.report_type,
        json.dumps(report.parameters),
        report.format,
        'generating'
    )

    # Generate report data
    report_data = await generate_report_data(report.report_type, report.parameters, conn)

    return {
        **dict(result),
        "id": str(result['id']),
        "data": report_data
    }

@router.get("/reports/templates")
async def get_report_templates(
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get available report templates"""
    templates = [
        {
            "id": "financial_summary",
            "name": "Financial Summary",
            "description": "Monthly financial performance report",
            "parameters": ["date_from", "date_to", "department"]
        },
        {
            "id": "sales_pipeline",
            "name": "Sales Pipeline Report",
            "description": "Current sales pipeline and forecast",
            "parameters": ["date_range", "sales_rep", "region"]
        },
        {
            "id": "customer_analysis",
            "name": "Customer Analysis",
            "description": "Customer segmentation and behavior analysis",
            "parameters": ["segment", "timeframe"]
        },
        {
            "id": "operational_metrics",
            "name": "Operational Metrics",
            "description": "Key operational performance indicators",
            "parameters": ["department", "metric_type", "period"]
        }
    ]
    return templates

@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = Query("pdf"),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Download generated report"""
    # In production, this would return actual file
    content = b"Report content here"

    media_type = {
        "pdf": "application/pdf",
        "excel": "application/vnd.ms-excel",
        "csv": "text/csv",
        "html": "text/html"
    }.get(format, "application/octet-stream")

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename=report_{report_id}.{format}"
        }
    )

async def generate_report_data(report_type: str, parameters: dict, conn) -> dict:
    """Generate report data based on type"""
    if report_type == "financial":
        query = """
            SELECT
                DATE_TRUNC('month', created_at) as month,
                SUM(total_amount) as revenue
            FROM invoices
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """
        rows = await conn.fetch(query)
        return {"monthly_revenue": [dict(row) for row in rows]}

    elif report_type == "sales":
        query = """
            SELECT
                COUNT(*) as total_opportunities,
                SUM(value) as pipeline_value,
                AVG(probability) as avg_probability
            FROM opportunities
            WHERE status = 'open'
        """
        result = await conn.fetchrow(query)
        return dict(result) if result else {}

    return {"message": "Report generated"}
