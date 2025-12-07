from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
import math
import json
import uuid
from datetime import datetime
from database.async_connection import get_pool

router = APIRouter(tags=["Gemini Estimation Engine"])

# --- MODELS ---

class GeometryData(BaseModel):
    type: str
    coordinates: Any

class FeatureInput(BaseModel):
    canvas_id: str
    type: str # polygon, line, point
    geometry: GeometryData
    name: Optional[str] = "New Feature"
    slope_pitch: Optional[str] = "0:12"
    assembly_id: Optional[str] = None

class CalculationResult(BaseModel):
    feature_id: str
    metrics: Dict[str, float]
    line_items: List[Dict[str, Any]]
    total_cost: float

# --- CORE LOGIC ---

def calculate_slope_factor(pitch: str) -> float:
    """Converts '4:12' to a multiplier (e.g. 1.054)"""
    if not pitch or ":" not in pitch:
        return 1.0
    try:
        rise = float(pitch.split(":")[0])
        run = 12.0
        hypotenuse = math.sqrt(rise**2 + run**2)
        return hypotenuse / run
    except:
        return 1.0

def calculate_polygon_area(coords: List[List[float]]) -> float:
    """Shoelace formula for area of a polygon (simple planar)"""
    n = len(coords)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    return abs(area) / 2.0

def calculate_line_length(coords: List[List[float]]) -> float:
    """Euclidean distance for line string"""
    length = 0.0
    for i in range(len(coords) - 1):
        p1 = coords[i]
        p2 = coords[i+1]
        dist = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        length += dist
    return length

# --- ENDPOINTS ---

@router.post("/canvas/{estimate_id}")
async def create_canvas(estimate_id: str, mode: str = "geo"):
    pool = await get_pool()
    async with pool.acquire() as conn:
        canvas_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO gemini_takeoff_canvases (id, estimate_id, mode)
            VALUES ($1, $2, $3)
        """, canvas_id, estimate_id, mode)
        return {"id": canvas_id, "mode": mode}

@router.get("/assemblies/list")
async def list_assemblies():
    """Returns a simplified list of assemblies for dropdowns"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Note: Using roofing_assemblies_cache which was populated by intelligent builder
        rows = await conn.fetch("""
            SELECT id, assembly_name as name, total_cost_sqft 
            FROM roofing_assemblies_cache 
            ORDER BY assembly_name
        """)
        return [
            {
                "id": str(row['id']),
                "name": row['name'],
                "cost_sqft": float(row['total_cost_sqft']) if row['total_cost_sqft'] else 0.0
            }
            for row in rows
        ]

@router.post("/feature/calculate")
async def calculate_feature(feature: FeatureInput):
    """
    The 'Minimum In, Max Out' Engine.
    Takes geometry -> Applies Physics -> Explodes Assembly -> Returns Money.
    """
    
    # 1. Calculate Raw Metrics
    # NOTE: This assumes the coordinates are already projected/scaled to FEET or METERS
    # In a real app, we'd handle CRS projection here.
    # For this vertical slice, we assume the frontend sends "Feet" (Plan mode) or we accept raw Lat/Lon and converting is TODO.
    # Let's assume Plan Mode (Cartesian Feet) for the math to hold simple.
    
    raw_area = 0.0
    raw_len = 0.0
    
    geom_type = feature.geometry.type
    coords = feature.geometry.coordinates
    
    if geom_type == "Polygon":
        # Coords is [[[x,y], [x,y]...]] (list of rings)
        # We take the outer ring (index 0)
        raw_area = calculate_polygon_area(coords[0])
        # Perimeter is length of outer ring
        raw_len = calculate_line_length(coords[0])
        
    elif geom_type == "LineString":
        raw_len = calculate_line_length(coords)
        
    # 2. Apply Physics (Slope)
    slope_factor = calculate_slope_factor(feature.slope_pitch)
    final_area = raw_area * slope_factor
    
    # 3. Explode Assembly
    line_items = []
    total_cost = 0.0
    
    if feature.assembly_id:
        pool = await get_pool()
        # Querying the cache table as that's where the builder puts them
        assembly = await pool.fetchrow("""
            SELECT components, assembly_name FROM roofing_assemblies_cache WHERE id = $1
        """, feature.assembly_id)
        
        if assembly and assembly['components']:
            components = json.loads(assembly['components'])
            
            for comp in components:
                # Logic: Map unit type to metric
                qty = 0.0
                unit = comp.get('unit_type', 'ea')
                
                if unit in ['sqft', 'sq']:
                    qty = final_area
                    if unit == 'sq': qty /= 100.0
                elif unit in ['lf', 'ft']:
                    qty = raw_len
                elif unit == 'ea':
                    # Simplified: 1 ea per feature? Or based on area?
                    # Let's assume if it's a point feature, it's 1.
                    if geom_type == "Point":
                        qty = 1.0
                    else:
                        # Heuristic: Fasteners per sqft?
                        # This would need the 'coverage' logic from the legacy Excel analysis
                        # For now, keep it simple.
                        qty = final_area * 0.05 # e.g. 5 fasteners per sqft
                
                # Apply quantity multiplier from assembly def
                qty *= float(comp.get('quantity', 1.0))
                
                cost = qty * float(comp.get('unit_cost', 0.0))
                
                line_items.append({
                    "name": comp.get('product_name', 'Unknown Item'),
                    "quantity": round(qty, 2),
                    "unit": unit,
                    "unit_cost": comp.get('unit_cost', 0.0),
                    "extended_cost": round(cost, 2)
                })
                total_cost += cost
                
    return CalculationResult(
        feature_id=str(uuid.uuid4()), # Ephemeral ID for preview
        metrics={
            "area_flat": raw_area,
            "area_sloped": final_area,
            "perimeter": raw_len,
            "slope_factor": slope_factor
        },
        line_items=line_items,
        total_cost=round(total_cost, 2)
    )

@router.post("/feature/save")
async def save_feature(feature: FeatureInput):
    """Saves the feature and links the assembly"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        fid = str(uuid.uuid4())
        
        # Save Feature
        await conn.execute("""
            INSERT INTO gemini_takeoff_features (
                id, canvas_id, name, type, geometry, slope_pitch
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """, fid, feature.canvas_id, feature.name, feature.type, 
           json.dumps(feature.geometry.dict()), feature.slope_pitch)
           
        # Link Assembly
        if feature.assembly_id:
            await conn.execute("""
                INSERT INTO gemini_feature_assemblies (feature_id, assembly_id)
                VALUES ($1, $2)
            """, fid, feature.assembly_id)
            
        return {"id": fid, "status": "saved"}
