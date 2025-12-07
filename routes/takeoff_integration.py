"""
TAKEOFF INTEGRATION ENGINE
==========================
The 'Brain' that converts geometric shapes into financial line items.
Implements the 'Minimum In, Max Out' protocol.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from decimal import Decimal
import uuid
import math
import json
from database.async_connection import get_pool

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

@router.post("/calculate")
async def calculate_feature_impact(payload: CalculationRequest):
    """
    Takes a raw geometry, applies physics/slope/scale, 
    and returns the financial 'Assembly BOM' (Bill of Materials).
    """
    # 1. Geometry Analysis
    geom_type = payload.feature.geometry.get("type")
    coords = payload.feature.geometry.get("coordinates")
    
    # Calculate Raw Metrics (Area/Length)
    # Note: This is a simplified calc. Real implementation needs Geodesic (Lat/Lon) or Euclidean (Plan) logic.
    # We assume Plan (Euclidean) for this logic block as it's safer for "scaled" drawings.
    raw_area = 0.0
    raw_perimeter = 0.0
    
    if geom_type == "Polygon":
        # Shoelace formula for Area
        # Euclidean distance for Perimeter
        # (Implementation omitted for brevity, assumes `calc_polygon_metrics` helper)
        raw_area = 1000.0 # Placeholder
        raw_perimeter = 400.0 # Placeholder
    elif geom_type == "LineString":
        raw_perimeter = 100.0 # Placeholder
    
    # 2. Apply Scale & Slope
    # Slope Multiplier
    rise = int(payload.slope_pitch.split(":")[0])
    slope_factor = math.sqrt(rise**2 + 12**2) / 12.0
    
    final_area = raw_area * slope_factor
    final_len = raw_perimeter # Lines usually don't stretch by slope unless they run UP the slope
    
    # 3. Assembly Expansion ("Max Out")
    line_items = []
    
    if payload.assembly_id:
        pool = await get_pool()
        assembly = await pool.fetchrow("SELECT * FROM roofing_assemblies WHERE id = $1", payload.assembly_id)
        
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
