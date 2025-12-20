"""
Opportunity Tracking Module - Task 62
Complete sales opportunity management system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum
from decimal import Decimal
import asyncpg
import uuid
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Database connection
async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


# Enums
class OpportunityStage(str, Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class OpportunityType(str, Enum):
    NEW_BUSINESS = "new_business"
    EXISTING_BUSINESS = "existing_business"
    RENEWAL = "renewal"
    UPGRADE = "upgrade"
    REPLACEMENT = "replacement"

class ForecastCategory(str, Enum):
    PIPELINE = "pipeline"
    BEST_CASE = "best_case"
    COMMIT = "commit"
    CLOSED = "closed"
    OMITTED = "omitted"

# Models
class OpportunityBase(BaseModel):
    opportunity_name: str = Field(..., min_length=1, max_length=200)
    account_id: Optional[str] = None
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    stage: OpportunityStage
    amount: float = Field(..., gt=0)
    close_date: date
    opportunity_type: Optional[OpportunityType] = None
    lead_source: Optional[str] = Field(None, max_length=100)
    next_step: Optional[str] = None
    description: Optional[str] = None
    competitor_names: Optional[List[str]] = []
    assigned_to: str = Field(..., min_length=1, max_length=100)
    territory_id: Optional[str] = None
    campaign_id: Optional[str] = None

class OpportunityCreate(OpportunityBase):
    pass

class OpportunityUpdate(BaseModel):
    opportunity_name: Optional[str] = Field(None, min_length=1, max_length=200)
    stage: Optional[OpportunityStage] = None
    amount: Optional[float] = Field(None, gt=0)
    close_date: Optional[date] = None
    next_step: Optional[str] = None
    description: Optional[str] = None
    competitor_names: Optional[List[str]] = None
    forecast_category: Optional[ForecastCategory] = None

class OpportunityResponse(OpportunityBase):
    id: str
    opportunity_number: str
    probability: int
    expected_revenue: float
    forecast_category: Optional[ForecastCategory] = None
    is_closed: bool = False
    is_won: bool = False
    closed_date: Optional[date] = None
    lost_reason: Optional[str] = None
    lost_to_competitor: Optional[str] = None
    contract_id: Optional[str] = None
    tags: Optional[List[str]] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

class OpportunityProduct(BaseModel):
    product_id: Optional[str] = None
    product_name: str = Field(..., min_length=1, max_length=200)
    product_code: Optional[str] = Field(None, max_length=100)
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    discount_percentage: float = Field(0, ge=0, le=100)
    description: Optional[str] = None

class OpportunityProductResponse(OpportunityProduct):
    id: str
    opportunity_id: str
    total_price: float
    discount_amount: float
    created_at: datetime

class StageUpdate(BaseModel):
    new_stage: OpportunityStage
    notes: Optional[str] = None

# Helper functions
async def generate_opportunity_number(conn: asyncpg.Connection) -> str:
    """Generate unique opportunity number"""
    count = await conn.fetchval("SELECT COUNT(*) FROM opportunities")
    year = datetime.utcnow().year
    return f"OPP-{year}-{(count or 0) + 1:05d}"

def calculate_probability(stage: str) -> int:
    """Calculate probability based on stage"""
    probabilities = {
        "prospecting": 10,
        "qualification": 20,
        "needs_analysis": 40,
        "proposal": 60,
        "negotiation": 80,
        "closed_won": 100,
        "closed_lost": 0
    }
    return probabilities.get(stage, 0)

def calculate_expected_revenue(amount: float, probability: int) -> float:
    """Calculate expected revenue"""
    return round(amount * (probability / 100), 2)

def determine_forecast_category(stage: str, close_date: date, amount: float) -> str:
    """Determine forecast category based on stage and close date"""
    days_to_close = (close_date - date.today()).days

    if stage == "closed_won":
        return ForecastCategory.CLOSED
    elif stage == "closed_lost":
        return ForecastCategory.OMITTED
    elif stage in ["negotiation", "proposal"] and days_to_close <= 30:
        return ForecastCategory.COMMIT
    elif stage in ["needs_analysis", "qualification"] and days_to_close <= 90:
        return ForecastCategory.BEST_CASE
    else:
        return ForecastCategory.PIPELINE

# CRUD Endpoints
@router.post("/", response_model=OpportunityResponse)
async def create_opportunity(
    opportunity: OpportunityCreate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new opportunity"""
    try:
        opportunity_number = await generate_opportunity_number(conn)
        probability = calculate_probability(opportunity.stage)
        expected_revenue = calculate_expected_revenue(opportunity.amount, probability)
        forecast_category = determine_forecast_category(
            opportunity.stage,
            opportunity.close_date,
            opportunity.amount
        )

        query = """
            INSERT INTO opportunities (
                opportunity_number, opportunity_name, account_id, lead_id,
                customer_id, stage, probability, amount, expected_revenue,
                close_date, opportunity_type, lead_source, next_step,
                description, competitor_names, assigned_to, territory_id,
                campaign_id, forecast_category, created_by
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                $14, $15, $16, $17, $18, $19, $20
            ) RETURNING *
        """

        result = await conn.fetchrow(
            query,
            opportunity_number,
            opportunity.opportunity_name,
            uuid.UUID(opportunity.account_id) if opportunity.account_id else None,
            uuid.UUID(opportunity.lead_id) if opportunity.lead_id else None,
            uuid.UUID(opportunity.customer_id) if opportunity.customer_id else None,
            opportunity.stage,
            probability,
            opportunity.amount,
            expected_revenue,
            opportunity.close_date,
            opportunity.opportunity_type,
            opportunity.lead_source,
            opportunity.next_step,
            opportunity.description,
            opportunity.competitor_names,
            opportunity.assigned_to,
            uuid.UUID(opportunity.territory_id) if opportunity.territory_id else None,
            uuid.UUID(opportunity.campaign_id) if opportunity.campaign_id else None,
            forecast_category,
            "system"
        )

        # Track opportunity creation
        background_tasks.add_task(
            track_opportunity_stage_change,
            str(result['id']),
            None,
            opportunity.stage,
            "Opportunity created",
            "system"
        )

        return format_opportunity_response(result)

    except Exception as e:
        logger.error(f"Error creating opportunity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[OpportunityResponse])
async def list_opportunities(
    stage: Optional[OpportunityStage] = None,
    assigned_to: Optional[str] = None,
    is_closed: Optional[bool] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    close_date_from: Optional[date] = None,
    close_date_to: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List opportunities with filters"""
    try:
        conditions = []
        params = []
        param_count = 0

        if stage:
            param_count += 1
            conditions.append(f"stage = ${param_count}")
            params.append(stage)

        if assigned_to:
            param_count += 1
            conditions.append(f"assigned_to = ${param_count}")
            params.append(assigned_to)

        if is_closed is not None:
            param_count += 1
            conditions.append(f"is_closed = ${param_count}")
            params.append(is_closed)

        if min_amount is not None:
            param_count += 1
            conditions.append(f"amount >= ${param_count}")
            params.append(min_amount)

        if max_amount is not None:
            param_count += 1
            conditions.append(f"amount <= ${param_count}")
            params.append(max_amount)

        if close_date_from:
            param_count += 1
            conditions.append(f"close_date >= ${param_count}")
            params.append(close_date_from)

        if close_date_to:
            param_count += 1
            conditions.append(f"close_date <= ${param_count}")
            params.append(close_date_to)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        param_count += 1
        limit_param = f"${param_count}"
        params.append(limit)

        param_count += 1
        offset_param = f"${param_count}"
        params.append(skip)

        query = f"""
            SELECT * FROM opportunities
            {where_clause}
            ORDER BY close_date ASC, amount DESC
            LIMIT {limit_param} OFFSET {offset_param}
        """

        rows = await conn.fetch(query, *params)

        return [format_opportunity_response(row) for row in rows]

    except Exception as e:
        logger.error(f"Error listing opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pipeline", response_model=Dict[str, Any])
async def get_pipeline_summary(
    assigned_to: Optional[str] = None,
    territory_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get pipeline summary by stage"""
    try:
        conditions = ["is_closed = false"]
        params = []

        if assigned_to:
            params.append(assigned_to)
            conditions.append(f"assigned_to = ${len(params)}")

        if territory_id:
            params.append(uuid.UUID(territory_id))
            conditions.append(f"territory_id = ${len(params)}")

        if date_from:
            params.append(date_from)
            conditions.append(f"close_date >= ${len(params)}")

        if date_to:
            params.append(date_to)
            conditions.append(f"close_date <= ${len(params)}")

        where_clause = f"WHERE {' AND '.join(conditions)}"

        query = f"""
            SELECT
                stage,
                COUNT(*) as count,
                SUM(amount) as total_amount,
                SUM(expected_revenue) as total_expected,
                AVG(amount) as avg_deal_size,
                AVG(probability) as avg_probability
            FROM opportunities
            {where_clause}
            GROUP BY stage
            ORDER BY
                CASE stage
                    WHEN 'prospecting' THEN 1
                    WHEN 'qualification' THEN 2
                    WHEN 'needs_analysis' THEN 3
                    WHEN 'proposal' THEN 4
                    WHEN 'negotiation' THEN 5
                    ELSE 6
                END
        """

        rows = await conn.fetch(query, *params)

        # Get totals
        total_query = f"""
            SELECT
                COUNT(*) as total_count,
                SUM(amount) as total_pipeline,
                SUM(expected_revenue) as total_weighted
            FROM opportunities
            {where_clause}
        """

        totals = await conn.fetchrow(total_query, *params)

        return {
            "stages": [
                {
                    "stage": row['stage'],
                    "count": row['count'],
                    "total_amount": float(row['total_amount'] or 0),
                    "total_expected": float(row['total_expected'] or 0),
                    "avg_deal_size": float(row['avg_deal_size'] or 0),
                    "avg_probability": float(row['avg_probability'] or 0)
                }
                for row in rows
            ],
            "totals": {
                "count": totals['total_count'],
                "pipeline_value": float(totals['total_pipeline'] or 0),
                "weighted_value": float(totals['total_weighted'] or 0)
            }
        }

    except Exception as e:
        logger.error(f"Error getting pipeline summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get opportunity by ID"""
    try:
        query = "SELECT * FROM opportunities WHERE id = $1"
        row = await conn.fetchrow(query, uuid.UUID(opportunity_id))

        if not row:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        return format_opportunity_response(row)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid opportunity ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting opportunity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: str,
    updates: OpportunityUpdate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update opportunity"""
    try:
        # Check if opportunity exists
        existing = await conn.fetchrow(
            "SELECT * FROM opportunities WHERE id = $1",
            uuid.UUID(opportunity_id)
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        # Build update query
        update_data = updates.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No updates provided")

        # Recalculate probability and expected revenue if stage changed
        if 'stage' in update_data:
            update_data['probability'] = calculate_probability(update_data['stage'])
            amount = update_data.get('amount', existing['amount'])
            update_data['expected_revenue'] = calculate_expected_revenue(
                amount, update_data['probability']
            )

            # Update closed status
            if update_data['stage'] == 'closed_won':
                update_data['is_closed'] = True
                update_data['is_won'] = True
                update_data['closed_date'] = date.today()
            elif update_data['stage'] == 'closed_lost':
                update_data['is_closed'] = True
                update_data['is_won'] = False
                update_data['closed_date'] = date.today()

        # Recalculate forecast category
        stage = update_data.get('stage', existing['stage'])
        close_date = update_data.get('close_date', existing['close_date'])
        amount = update_data.get('amount', existing['amount'])
        update_data['forecast_category'] = determine_forecast_category(stage, close_date, amount)

        set_clauses = []
        params = []
        param_count = 0

        for field, value in update_data.items():
            param_count += 1
            set_clauses.append(f"{field} = ${param_count}")
            params.append(value)

        param_count += 1
        set_clauses.append(f"updated_at = ${param_count}")
        params.append(datetime.utcnow())

        param_count += 1
        set_clauses.append(f"updated_by = ${param_count}")
        params.append("system")

        param_count += 1
        query = f"""
            UPDATE opportunities
            SET {', '.join(set_clauses)}
            WHERE id = ${param_count}
            RETURNING *
        """
        params.append(uuid.UUID(opportunity_id))

        result = await conn.fetchrow(query, *params)

        # Track stage change
        if 'stage' in update_data and update_data['stage'] != existing['stage']:
            background_tasks.add_task(
                track_opportunity_stage_change,
                opportunity_id,
                existing['stage'],
                update_data['stage'],
                None,
                "system"
            )

        return format_opportunity_response(result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating opportunity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{opportunity_id}/stage", response_model=OpportunityResponse)
async def update_opportunity_stage(
    opportunity_id: str,
    stage_update: StageUpdate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update opportunity stage with tracking"""
    try:
        # Get current opportunity
        existing = await conn.fetchrow(
            "SELECT * FROM opportunities WHERE id = $1",
            uuid.UUID(opportunity_id)
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        # Calculate new values
        probability = calculate_probability(stage_update.new_stage)
        expected_revenue = calculate_expected_revenue(existing['amount'], probability)
        forecast_category = determine_forecast_category(
            stage_update.new_stage,
            existing['close_date'],
            existing['amount']
        )

        # Prepare update values
        update_values = {
            'stage': stage_update.new_stage,
            'probability': probability,
            'expected_revenue': expected_revenue,
            'forecast_category': forecast_category
        }

        # Handle closed stages
        if stage_update.new_stage == 'closed_won':
            update_values.update({
                'is_closed': True,
                'is_won': True,
                'closed_date': date.today()
            })
        elif stage_update.new_stage == 'closed_lost':
            update_values.update({
                'is_closed': True,
                'is_won': False,
                'closed_date': date.today()
            })

        # Update opportunity
        query = """
            UPDATE opportunities
            SET stage = $1, probability = $2, expected_revenue = $3,
                forecast_category = $4, is_closed = $5, is_won = $6,
                closed_date = $7, updated_at = $8, updated_by = $9
            WHERE id = $10
            RETURNING *
        """

        result = await conn.fetchrow(
            query,
            update_values['stage'],
            update_values['probability'],
            update_values['expected_revenue'],
            update_values['forecast_category'],
            update_values.get('is_closed', existing['is_closed']),
            update_values.get('is_won', existing['is_won']),
            update_values.get('closed_date', existing['closed_date']),
            datetime.utcnow(),
            "system",
            uuid.UUID(opportunity_id)
        )

        # Track stage change
        background_tasks.add_task(
            track_opportunity_stage_change,
            opportunity_id,
            existing['stage'],
            stage_update.new_stage,
            stage_update.notes,
            "system"
        )

        return format_opportunity_response(result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating stage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{opportunity_id}/products", response_model=OpportunityProductResponse)
async def add_opportunity_product(
    opportunity_id: str,
    product: OpportunityProduct,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Add product to opportunity"""
    try:
        # Check opportunity exists
        opp_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM opportunities WHERE id = $1)",
            uuid.UUID(opportunity_id)
        )
        if not opp_exists:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        # Calculate prices
        discount_amount = product.unit_price * product.quantity * (product.discount_percentage / 100)
        total_price = (product.unit_price * product.quantity) - discount_amount

        query = """
            INSERT INTO opportunity_products (
                opportunity_id, product_id, product_name, product_code,
                quantity, unit_price, total_price, discount_percentage,
                discount_amount, description
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *
        """

        result = await conn.fetchrow(
            query,
            uuid.UUID(opportunity_id),
            uuid.UUID(product.product_id) if product.product_id else None,
            product.product_name,
            product.product_code,
            product.quantity,
            product.unit_price,
            total_price,
            product.discount_percentage,
            discount_amount,
            product.description
        )

        # Update opportunity amount
        await update_opportunity_amount(conn, opportunity_id)

        return {
            **dict(result),
            "id": str(result['id']),
            "opportunity_id": str(result['opportunity_id']),
            "product_id": str(result['product_id']) if result['product_id'] else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{opportunity_id}/products", response_model=List[OpportunityProductResponse])
async def get_opportunity_products(
    opportunity_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get products for an opportunity"""
    try:
        query = """
            SELECT * FROM opportunity_products
            WHERE opportunity_id = $1
            ORDER BY created_at
        """

        rows = await conn.fetch(query, uuid.UUID(opportunity_id))

        return [
            {
                **dict(row),
                "id": str(row['id']),
                "opportunity_id": str(row['opportunity_id']),
                "product_id": str(row['product_id']) if row['product_id'] else None
            }
            for row in rows
        ]

    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_opportunity_stats(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    assigned_to: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get opportunity statistics"""
    try:
        conditions = []
        params = []

        if date_from:
            params.append(date_from)
            conditions.append(f"created_at >= ${len(params)}")

        if date_to:
            params.append(date_to + timedelta(days=1))
            conditions.append(f"created_at < ${len(params)}")

        if assigned_to:
            params.append(assigned_to)
            conditions.append(f"assigned_to = ${len(params)}")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT
                COUNT(*) as total_opportunities,
                COUNT(CASE WHEN is_won THEN 1 END) as won_deals,
                COUNT(CASE WHEN is_closed AND NOT is_won THEN 1 END) as lost_deals,
                COUNT(CASE WHEN NOT is_closed THEN 1 END) as open_deals,
                SUM(CASE WHEN is_won THEN amount ELSE 0 END) as total_won,
                SUM(CASE WHEN NOT is_closed THEN amount ELSE 0 END) as pipeline_value,
                SUM(CASE WHEN NOT is_closed THEN expected_revenue ELSE 0 END) as weighted_pipeline,
                AVG(amount) as avg_deal_size,
                AVG(CASE WHEN is_closed THEN
                    EXTRACT(DAY FROM closed_date - created_at)
                END) as avg_days_to_close
            FROM opportunities
            {where_clause}
        """

        result = await conn.fetchrow(query, *params)

        # Calculate win rate
        total_closed = (result['won_deals'] or 0) + (result['lost_deals'] or 0)
        win_rate = ((result['won_deals'] or 0) / total_closed * 100) if total_closed > 0 else 0

        return {
            **dict(result),
            "win_rate": round(win_rate, 2),
            "total_won": float(result['total_won'] or 0),
            "pipeline_value": float(result['pipeline_value'] or 0),
            "weighted_pipeline": float(result['weighted_pipeline'] or 0),
            "avg_deal_size": float(result['avg_deal_size'] or 0),
            "avg_days_to_close": float(result['avg_days_to_close'] or 0)
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def format_opportunity_response(row: dict) -> dict:
    """Format opportunity response"""
    return {
        **dict(row),
        "id": str(row['id']),
        "account_id": str(row['account_id']) if row['account_id'] else None,
        "lead_id": str(row['lead_id']) if row['lead_id'] else None,
        "customer_id": str(row['customer_id']) if row['customer_id'] else None,
        "territory_id": str(row['territory_id']) if row['territory_id'] else None,
        "campaign_id": str(row['campaign_id']) if row['campaign_id'] else None,
        "contract_id": str(row['contract_id']) if row['contract_id'] else None,
        "amount": float(row['amount']),
        "expected_revenue": float(row['expected_revenue'] or 0)
    }

async def update_opportunity_amount(conn: asyncpg.Connection, opportunity_id: str):
    """Update opportunity amount based on products"""
    try:
        query = """
            UPDATE opportunities
            SET amount = (
                SELECT COALESCE(SUM(total_price), 0)
                FROM opportunity_products
                WHERE opportunity_id = $1
            ),
            updated_at = $2
            WHERE id = $1
        """
        await conn.execute(query, uuid.UUID(opportunity_id), datetime.utcnow())
    except Exception as e:
        logger.error(f"Error updating opportunity amount: {e}")

async def track_opportunity_stage_change(
    opportunity_id: str,
    from_stage: Optional[str],
    to_stage: str,
    notes: Optional[str],
    user: str
):
    """Background task to track stage changes"""
    try:
        conn = await asyncpg.connect(
            host="aws-0-us-east-2.pooler.supabase.com",
            port=5432,
            user="postgres.yomagoqdmxszqtdwuhab",
            password="<DB_PASSWORD_REDACTED>",
            database="postgres"
        )
        try:
            # Get pipeline ID (use default)
            pipeline_id = await conn.fetchval(
                "SELECT id FROM sales_pipelines WHERE is_default = true LIMIT 1"
            )

            if not pipeline_id:
                # Create default pipeline if doesn't exist
                pipeline_id = await conn.fetchval(
                    """
                    INSERT INTO sales_pipelines (
                        pipeline_name, pipeline_type, is_default, stages
                    ) VALUES (
                        'Default Pipeline', 'standard', true, $1
                    ) RETURNING id
                    """,
                    json.dumps([
                        "prospecting", "qualification", "needs_analysis",
                        "proposal", "negotiation", "closed_won", "closed_lost"
                    ])
                )

            # Calculate duration in previous stage
            duration_days = None
            if from_stage:
                last_change = await conn.fetchval(
                    """
                    SELECT changed_at FROM pipeline_stage_history
                    WHERE opportunity_id = $1
                    ORDER BY changed_at DESC LIMIT 1
                    """,
                    uuid.UUID(opportunity_id)
                )
                if last_change:
                    duration_days = (datetime.utcnow() - last_change).days

            # Insert stage history
            await conn.execute(
                """
                INSERT INTO pipeline_stage_history (
                    opportunity_id, pipeline_id, from_stage, to_stage,
                    changed_by, duration_in_stage_days, notes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                uuid.UUID(opportunity_id),
                pipeline_id,
                from_stage,
                to_stage,
                user,
                duration_days,
                notes
            )
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error tracking stage change: {e}")