"""
Customer Search and Filter Engine
Advanced search capabilities with faceted filtering and full-text search
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import logging
from enum import Enum

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from services.audit_service import log_data_access

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/customers/search", tags=["Customer Search"])

# ============================================================================
# ENUMS AND MODELS
# ============================================================================

class SearchOperator(str, Enum):
    EQUALS = "eq"
    NOT_EQUALS = "neq"
    CONTAINS = "contains"
    STARTS_WITH = "starts"
    ENDS_WITH = "ends"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"

class SearchField(str, Enum):
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    COMPANY = "company"
    ADDRESS = "address"
    CITY = "city"
    STATE = "state"
    ZIP_CODE = "zip_code"
    STATUS = "status"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    TOTAL_REVENUE = "total_revenue"
    JOB_COUNT = "job_count"
    TAG = "tag"
    CUSTOM_FIELD = "custom_field"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================

@router.post("/advanced")
async def advanced_search(
    filters: List[Dict[str, Any]],
    sort_by: str = Query("created_at"),
    sort_order: SortOrder = Query(SortOrder.DESC),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Advanced search with multiple filters and operators
    
    Filters format:
    [
        {"field": "name", "operator": "contains", "value": "john"},
        {"field": "total_revenue", "operator": "gt", "value": 10000},
        {"field": "state", "operator": "in", "value": ["CA", "NY"]}
    ]
    """
    try:
        # Build base query with aggregates
        base_query = """
            SELECT 
                c.*,
                COUNT(DISTINCT j.id) as job_count,
                COALESCE(SUM(j.total_amount), 0) as total_revenue,
                COUNT(DISTINCT i.id) as invoice_count,
                MAX(j.created_at) as last_job_date
            FROM customers c
            LEFT JOIN jobs j ON c.id = j.customer_id
            LEFT JOIN invoices i ON c.id = i.customer_id
        """

        # Build WHERE conditions
        conditions = []
        params = {}
        param_counter = 0

        for filter_item in filters:
            field = filter_item.get("field")
            operator = filter_item.get("operator")
            value = filter_item.get("value")
            param_name = f"param_{param_counter}"
            param_counter += 1

            condition = _build_condition(field, operator, value, param_name)
            if condition:
                conditions.append(condition)
                if value is not None and operator not in ["is_null", "is_not_null"]:
                    params[param_name] = value

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        # Add GROUP BY and ORDER BY
        query = base_query + where_clause + " GROUP BY c.id "

        # Whitelist allowed sort columns to prevent SQL injection
        allowed_sort_columns = {"name": "c.name", "email": "c.email", "created_at": "c.created_at", "updated_at": "c.updated_at", "total_revenue": "total_revenue", "job_count": "job_count"}
        safe_sort_by = allowed_sort_columns.get(sort_by, "c.created_at")
        safe_sort_order = "DESC" if sort_order.value.upper() == "DESC" else "ASC"
        query += f" ORDER BY {safe_sort_by} {safe_sort_order} "
        query += " LIMIT :limit OFFSET :offset"

        params["limit"] = per_page
        params["offset"] = (page - 1) * per_page

        # Execute main query
        result = db.execute(text(query), params)
        customers = []
        for row in result:
            customer = dict(row._mapping)
            customer["id"] = str(customer["id"])
            customers.append(customer)

        # Get total count
        count_query = f"""
            SELECT COUNT(DISTINCT c.id)
            FROM customers c
            LEFT JOIN jobs j ON c.id = j.customer_id
            {where_clause}
        """
        count_params = {k: v for k, v in params.items() if k not in ["limit", "offset"]}
        total = db.execute(text(count_query), count_params).scalar()

        log_data_access(db, current_user["id"], "customers", "advanced_search", len(customers))

        return {
            "customers": customers,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
            "filters_applied": len(filters)
        }

    except Exception as e:
        logger.error(f"Advanced search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/quick")
async def quick_search(
    q: str = Query(..., min_length=2),
    fields: Optional[List[SearchField]] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Quick search across multiple fields
    Returns top matches with relevance scoring
    """
    try:
        # Default search fields if none specified
        if not fields:
            fields = [SearchField.NAME, SearchField.EMAIL, SearchField.COMPANY, SearchField.PHONE]

        # Build search conditions
        search_conditions = []
        for field in fields:
            search_conditions.append(f"c.{field.value} ILIKE :search_term")

        where_clause = " OR ".join(search_conditions)

        # Query with relevance scoring
        query = f"""
            SELECT 
                c.*,
                COUNT(DISTINCT j.id) as job_count,
                COALESCE(SUM(j.total_amount), 0) as total_revenue,
                CASE
                    WHEN c.name ILIKE :exact_term THEN 100
                    WHEN c.email ILIKE :exact_term THEN 90
                    WHEN c.company ILIKE :exact_term THEN 80
                    WHEN c.name ILIKE :search_term THEN 70
                    WHEN c.email ILIKE :search_term THEN 60
                    WHEN c.company ILIKE :search_term THEN 50
                    ELSE 40
                END as relevance_score
            FROM customers c
            LEFT JOIN jobs j ON c.id = j.customer_id
            WHERE {where_clause}
            GROUP BY c.id
            ORDER BY relevance_score DESC, c.created_at DESC
            LIMIT :limit
        """

        params = {
            "search_term": f"%{q}%",
            "exact_term": q,
            "limit": limit
        }

        result = db.execute(text(query), params)

        customers = []
        for row in result:
            customer = dict(row._mapping)
            customer["id"] = str(customer["id"])
            customers.append(customer)

        log_data_access(db, current_user["id"], "customers", "quick_search", len(customers))

        return {
            "results": customers,
            "query": q,
            "fields_searched": [f.value for f in fields],
            "count": len(customers)
        }

    except Exception as e:
        logger.error(f"Quick search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/facets")
async def get_search_facets(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get faceted search options with counts
    Used for building filter UI with available options
    """
    try:
        facets = {}

        # Status facet
        status_result = db.execute(
            text("""
                SELECT status, COUNT(*) as count
                FROM customers
                WHERE status != 'deleted'
                GROUP BY status
                ORDER BY count DESC
            """)
        )
        facets["status"] = [dict(row._mapping) for row in status_result]

        # State facet
        state_result = db.execute(
            text("""
                SELECT state, COUNT(*) as count
                FROM customers
                WHERE state IS NOT NULL AND status != 'deleted'
                GROUP BY state
                ORDER BY count DESC
                LIMIT 20
            """)
        )
        facets["state"] = [dict(row._mapping) for row in state_result]

        # City facet (top 20)
        city_result = db.execute(
            text("""
                SELECT city, COUNT(*) as count
                FROM customers
                WHERE city IS NOT NULL AND status != 'deleted'
                GROUP BY city
                ORDER BY count DESC
                LIMIT 20
            """)
        )
        facets["city"] = [dict(row._mapping) for row in city_result]

        # Revenue ranges
        revenue_result = db.execute(
            text("""
                SELECT
                    CASE
                        WHEN total_revenue = 0 THEN 'No Revenue'
                        WHEN total_revenue < 1000 THEN 'Under $1K'
                        WHEN total_revenue < 5000 THEN '$1K - $5K'
                        WHEN total_revenue < 10000 THEN '$5K - $10K'
                        WHEN total_revenue < 50000 THEN '$10K - $50K'
                        ELSE 'Over $50K'
                    END as range,
                    COUNT(*) as count
                FROM (
                    SELECT c.id, COALESCE(SUM(j.total_amount), 0) as total_revenue
                    FROM customers c
                    LEFT JOIN jobs j ON c.id = j.customer_id
                    WHERE c.status != 'deleted'
                    GROUP BY c.id
                ) revenue_data
                GROUP BY range
                ORDER BY 
                    CASE range
                        WHEN 'No Revenue' THEN 1
                        WHEN 'Under $1K' THEN 2
                        WHEN '$1K - $5K' THEN 3
                        WHEN '$5K - $10K' THEN 4
                        WHEN '$10K - $50K' THEN 5
                        ELSE 6
                    END
            """)
        )
        facets["revenue_range"] = [dict(row._mapping) for row in revenue_result]

        # Tags (top 20)
        tags_result = db.execute(
            text("""
                SELECT jsonb_array_elements_text(tags) as tag, COUNT(*) as count
                FROM customers
                WHERE tags IS NOT NULL AND status != 'deleted'
                GROUP BY tag
                ORDER BY count DESC
                LIMIT 20
            """)
        )
        facets["tags"] = [dict(row._mapping) for row in tags_result]

        # Date ranges
        date_result = db.execute(
            text("""
                SELECT
                    'Last 7 days' as period,
                    COUNT(*) as count
                FROM customers
                WHERE created_at >= NOW() - INTERVAL '7 days'
                    AND status != 'deleted'
                UNION ALL
                SELECT
                    'Last 30 days' as period,
                    COUNT(*) as count
                FROM customers
                WHERE created_at >= NOW() - INTERVAL '30 days'
                    AND status != 'deleted'
                UNION ALL
                SELECT
                    'Last 90 days' as period,
                    COUNT(*) as count
                FROM customers
                WHERE created_at >= NOW() - INTERVAL '90 days'
                    AND status != 'deleted'
                UNION ALL
                SELECT
                    'Last year' as period,
                    COUNT(*) as count
                FROM customers
                WHERE created_at >= NOW() - INTERVAL '1 year'
                    AND status != 'deleted'
            """)
        )
        facets["date_ranges"] = [dict(row._mapping) for row in date_result]

        return facets

    except Exception as e:
        logger.error(f"Facet generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate facets")

@router.get("/saved")
async def get_saved_searches(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's saved search queries
    """
    try:
        result = db.execute(
            text("""
                SELECT id, name, filters, created_at, last_used
                FROM saved_searches
                WHERE user_id = :user_id
                ORDER BY last_used DESC NULLS LAST, created_at DESC
                LIMIT 20
            """),
            {"user_id": current_user["id"]}
        )

        searches = []
        for row in result:
            search = dict(row._mapping)
            search["id"] = str(search["id"])
            searches.append(search)

        return {"saved_searches": searches}

    except Exception as e:
        logger.error(f"Failed to fetch saved searches: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch saved searches")

@router.post("/save")
async def save_search(
    name: str,
    filters: List[Dict[str, Any]],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save a search query for later use
    """
    try:
        import json
        from uuid import uuid4

        search_id = str(uuid4())

        db.execute(
            text("""
                INSERT INTO saved_searches (id, user_id, name, filters, created_at)
                VALUES (:id, :user_id, :name, :filters::jsonb, NOW())
            """),
            {
                "id": search_id,
                "user_id": current_user["id"],
                "name": name,
                "filters": json.dumps(filters)
            }
        )

        db.commit()

        return {"id": search_id, "message": "Search saved successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save search: {e}")
        raise HTTPException(status_code=500, detail="Failed to save search")

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1),
    field: SearchField = Query(SearchField.NAME),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get autocomplete suggestions for search
    """
    try:
        # Whitelist allowed fields to prevent SQL injection
        allowed_fields = {"name": "name", "email": "email", "phone": "phone", "company": "company",
                         "address": "address", "city": "city", "state": "state", "zip_code": "zip_code",
                         "status": "status"}
        safe_field = allowed_fields.get(field.value, "name")

        query = f"""
            SELECT DISTINCT {safe_field} as suggestion,
                   COUNT(*) as frequency
            FROM customers
            WHERE {safe_field} ILIKE :term
                AND status != 'deleted'
            GROUP BY {safe_field}
            ORDER BY frequency DESC, {safe_field}
            LIMIT :limit
        """

        result = db.execute(
            text(query),
            {"term": f"{q}%", "limit": limit}
        )

        suggestions = []
        for row in result:
            suggestions.append({
                "value": row.suggestion,
                "frequency": row.frequency
            })

        return {
            "suggestions": suggestions,
            "field": field.value,
            "query": q
        }

    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _build_condition(field: str, operator: str, value: Any, param_name: str) -> str:
    """
    Build SQL condition based on field, operator, and value
    """
    # Map fields to table columns
    field_map = {
        "name": "c.name",
        "email": "c.email",
        "phone": "c.phone",
        "company": "c.company",
        "address": "c.address",
        "city": "c.city",
        "state": "c.state",
        "zip_code": "c.zip_code",
        "status": "c.status",
        "created_at": "c.created_at",
        "updated_at": "c.updated_at",
        "total_revenue": "COALESCE(SUM(j.total_amount), 0)",
        "job_count": "COUNT(DISTINCT j.id)"
    }

    column = field_map.get(field, f"c.{field}")

    # Build condition based on operator
    if operator == "eq":
        return f"{column} = :{param_name}"
    elif operator == "neq":
        return f"{column} != :{param_name}"
    elif operator == "contains":
        return f"{column} ILIKE '%' || :{param_name} || '%'"
    elif operator == "starts":
        return f"{column} ILIKE :{param_name} || '%'"
    elif operator == "ends":
        return f"{column} ILIKE '%' || :{param_name}"
    elif operator == "gt":
        return f"{column} > :{param_name}"
    elif operator == "gte":
        return f"{column} >= :{param_name}"
    elif operator == "lt":
        return f"{column} < :{param_name}"
    elif operator == "lte":
        return f"{column} <= :{param_name}"
    elif operator == "in":
        # Handle array values
        if isinstance(value, list):
            placeholders = ", ".join([f":{param_name}_{i}" for i in range(len(value))])
            return f"{column} IN ({placeholders})"
        return f"{column} = :{param_name}"
    elif operator == "not_in":
        if isinstance(value, list):
            placeholders = ", ".join([f":{param_name}_{i}" for i in range(len(value))])
            return f"{column} NOT IN ({placeholders})"
        return f"{column} != :{param_name}"
    elif operator == "between":
        # Expects value to be [min, max]
        if isinstance(value, list) and len(value) == 2:
            return f"{column} BETWEEN :{param_name}_0 AND :{param_name}_1"
    elif operator == "is_null":
        return f"{column} IS NULL"
    elif operator == "is_not_null":
        return f"{column} IS NOT NULL RETURNING *"

    return None
