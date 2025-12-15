"""
Customer Feedback Module - Task 84
Feedback collection and analysis
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import uuid
import json

router = APIRouter()

async def get_db():
    conn = await asyncpg.connect(
        host="aws-0-us-east-2.pooler.supabase.com",
        port=5432,
        user="postgres.yomagoqdmxszqtdwuhab",
        password="<DB_PASSWORD_REDACTED>",
        database="postgres"
    )
    try:
        yield conn
    finally:
        await conn.close()

class FeedbackCreate(BaseModel):
    customer_id: str
    feedback_type: str  # survey, rating, comment, complaint
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None
    category: str = "general"
    metadata: Optional[Dict[str, Any]] = {}

@router.post("/", response_model=dict)
async def submit_feedback(
    feedback: FeedbackCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Submit customer feedback"""
    query = """
        INSERT INTO customer_feedback (
            customer_id, feedback_type, rating, comment,
            category, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(feedback.customer_id),
        feedback.feedback_type,
        feedback.rating,
        feedback.comment,
        feedback.category,
        json.dumps(feedback.metadata)
    )

    # Calculate sentiment if comment provided
    sentiment = "neutral"
    if feedback.comment:
        sentiment = analyze_sentiment(feedback.comment)

    await conn.execute(
        "UPDATE customer_feedback SET sentiment = $1 WHERE id = $2",
        sentiment,
        result['id']
    )

    return {
        "id": str(result['id']),
        "status": "received",
        "sentiment": sentiment
    }

@router.get("/analytics", response_model=dict)
async def get_feedback_analytics(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get feedback analytics"""
    if not date_from:
        date_from = datetime.now() - timedelta(days=30)
    if not date_to:
        date_to = datetime.now()

    query = """
        SELECT
            COUNT(*) as total_feedback,
            AVG(rating) as average_rating,
            COUNT(CASE WHEN sentiment = 'positive' THEN 1 END) as positive,
            COUNT(CASE WHEN sentiment = 'negative' THEN 1 END) as negative,
            COUNT(CASE WHEN sentiment = 'neutral' THEN 1 END) as neutral
        FROM customer_feedback
        WHERE created_at BETWEEN $1 AND $2
    """

    result = await conn.fetchrow(query, date_from, date_to)

    return {
        **dict(result),
        "nps_score": calculate_nps(conn, date_from, date_to),
        "satisfaction_score": float(result['average_rating'] or 0) * 20
    }

@router.get("/surveys/{survey_id}/responses", response_model=List[dict])
async def get_survey_responses(
    survey_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get survey responses"""
    query = """
        SELECT * FROM customer_feedback
        WHERE feedback_type = 'survey'
        AND metadata->>'survey_id' = $1
        ORDER BY created_at DESC
    """

    rows = await conn.fetch(query, survey_id)
    return [
        {
            **dict(row),
            "id": str(row['id']),
            "customer_id": str(row['customer_id']),
            "metadata": json.loads(row.get('metadata', '{}'))
        } for row in rows
    ]

def analyze_sentiment(text: str) -> str:
    """Simple sentiment analysis"""
    positive_words = ['good', 'great', 'excellent', 'love', 'best', 'amazing']
    negative_words = ['bad', 'poor', 'terrible', 'hate', 'worst', 'awful']

    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)

    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    return "neutral"

async def calculate_nps(conn, date_from, date_to) -> float:
    """Calculate Net Promoter Score"""
    query = """
        SELECT rating, COUNT(*) as count
        FROM customer_feedback
        WHERE rating IS NOT NULL
        AND created_at BETWEEN $1 AND $2
        GROUP BY rating
    """

    rows = await conn.fetch(query, date_from, date_to)

    if not rows:
        return 0

    total = sum(row['count'] for row in rows)
    promoters = sum(row['count'] for row in rows if row['rating'] >= 9)
    detractors = sum(row['count'] for row in rows if row['rating'] <= 6)

    return ((promoters - detractors) / total) * 100 if total > 0 else 0
