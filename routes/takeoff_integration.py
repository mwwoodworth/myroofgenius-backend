"""
TAKEOFF INTEGRATION ENGINE
==========================
The 'Brain' that converts geometric shapes into financial line items.
Implements the 'Minimum In, Max Out' protocol.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from decimal import Decimal
import uuid
import math
import json
import logging
from database.async_connection import get_pool
from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/takeoff", tags=["Takeoff Intelligence"])

class GeoFeature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]

class CalculationRequest(BaseModel):
    feature: GeoFeature
    scale_factor: Optional[float] = 1.0 # Pixels per foot (for Plan mode)
    slope_pitch: Optional[str] = "0:12" # e.g., "4:12"
    assembly_id: Optional[str] = None


def _ensure_closed_ring(points: List[List[float]]) -> List[List[float]]:
    if not points:
        return points
    if points[0] != points[-1]:
        return points + [points[0]]
    return points


def _polygon_area_and_perimeter(points: List[List[float]]) -> tuple[float, float]:
    """Compute planar polygon area and perimeter for a single ring."""
    points = _ensure_closed_ring(points)
    if len(points) < 4:
        return 0.0, 0.0
    area2 = 0.0
    perimeter = 0.0
    for (x1, y1), (x2, y2) in zip(points[:-1], points[1:]):
        area2 += (x1 * y2) - (x2 * y1)
        perimeter += math.hypot(x2 - x1, y2 - y1)
    return abs(area2) / 2.0, perimeter


def _linestring_length(points: List[List[float]]) -> float:
    if not points or len(points) < 2:
        return 0.0
    length = 0.0
    for (x1, y1), (x2, y2) in zip(points[:-1], points[1:]):
        length += math.hypot(x2 - x1, y2 - y1)
    return length


def _parse_slope_pitch(pitch: str) -> tuple[int, int]:
    """Parse slope pitch like '4:12' or '4/12'."""
    if not pitch:
        return 0, 12
    cleaned = pitch.replace("/", ":")
    parts = cleaned.split(":")
    if len(parts) != 2:
        return 0, 12
    try:
        rise = int(parts[0])
        run = int(parts[1])
        return rise, run if run else 12
    except ValueError:
        return 0, 12


@router.post("/calculate")
async def calculate_feature_impact(
    payload: CalculationRequest,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """
    Takes a raw geometry, applies physics/slope/scale, 
    and returns the financial 'Assembly BOM' (Bill of Materials).
    Requires Authentication.
    """
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context missing")

    # 1. Geometry Analysis
    geom_type = payload.feature.geometry.get("type")
    coords = payload.feature.geometry.get("coordinates")
    
    # Calculate Raw Metrics (Area/Length)
    raw_area = 0.0
    raw_perimeter = 0.0
    scale_factor = payload.scale_factor or 1.0
    if scale_factor <= 0:
        raise HTTPException(status_code=400, detail="scale_factor must be > 0")
    
    if geom_type == "Polygon":
        # Expect GeoJSON polygon: [ [ [x,y], ... ] , ... ]
        ring = (coords or [[]])[0] if isinstance(coords, list) else []
        area_units, perim_units = _polygon_area_and_perimeter(ring)
        # Convert from pixels^2 to sqft and pixels to feet.
        raw_area = area_units / (scale_factor**2)
        raw_perimeter = perim_units / scale_factor
    elif geom_type == "LineString":
        raw_perimeter = _linestring_length(coords or []) / scale_factor
    
    # 2. Apply Scale & Slope
    # Slope Multiplier
    rise, run = _parse_slope_pitch(payload.slope_pitch or "0:12")
    slope_factor = math.sqrt(rise**2 + run**2) / float(run)
    
    final_area = raw_area * slope_factor
    final_len = raw_perimeter # Lines usually don't stretch by slope unless they run UP the slope
    
    # 3. Assembly Expansion ("Max Out")
    line_items = []
    
    if payload.assembly_id:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Enforce Tenant Isolation (Own assemblies OR System assemblies)
            assembly = await conn.fetchrow(
                """
                SELECT * FROM roofing_assemblies 
                WHERE id = $1 AND (tenant_id = $2 OR tenant_id IS NULL)
                """, 
                payload.assembly_id, 
                tenant_id
            )
            
            if assembly:
                components = json.loads(assembly['components'] or '[]')
                
                for comp in components:
                    # "Minimum In" -> "Max Out" Logic
                    # If component unit is 'sqft', multiply by Area
                    # If component unit is 'lf', multiply by Perimeter
                    
                    qty = 0
                    if comp['unit_type'] == 'sqft':
                        qty = final_area * float(comp.get('quantity', 1.0))
                    elif comp['unit_type'] == 'lf':
                        qty = final_len * float(comp.get('quantity', 1.0))
                    elif comp['unit_type'] == 'ea':
                        # Complex logic: e.g., "1 screw per 2 sqft"
                        rate = float(comp.get('quantity', 1.0))
                        # Heuristic: If rate is small (<1), it's likely 'per sqft'
                        qty = final_area * rate 
                    
                    line_items.append({
                        "name": comp['product_name'],
                        "quantity": round(qty, 2),
                        "unit": comp['unit_type'],
                        "unit_cost": comp['unit_cost'],
                        "extended_cost": round(qty * float(comp['unit_cost']), 2)
                    })
            else:
                 logger.warning(f"Assembly {payload.assembly_id} not found for tenant {tenant_id}")

    return {
        "metrics": {
            "area_flat": raw_area,
            "area_sloped": final_area,
            "perimeter": final_len,
            "slope_factor": slope_factor
        },
        "bill_of_materials": line_items,
        "total_estimated_cost": sum(item['extended_cost'] for item in line_items)
    }
