"""
Elena Roofing AI Agent - API Routes
Enterprise-grade roofing estimation agent
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/elena", tags=["Elena AI Agent"])

# Request/Response Models
class AssemblyRequest(BaseModel):
    system_type: str  # TPO, EPDM, PVC, ModifiedBitumen, BuiltUp, Metal
    deck_type: str  # concrete, steel, wood, lightweight_concrete
    wind_zone_psf: float  # Wind uplift in PSF
    fm_approval_required: Optional[str] = None  # 1-60, 1-75, 1-90, 1-120, 1-135
    warranty_years: int = 20  # 10, 15, 20, 25, 30
    r_value_required: Optional[float] = None  # Thermal resistance
    cool_roof_required: bool = False
    budget_tier: str = "standard"  # economy, standard, premium
    preferred_manufacturer: Optional[str] = None
    tenant_id: Optional[str] = None

class RecommendationRequest(BaseModel):
    system_type: str
    deck_type: str
    wind_zone_psf: float
    fm_approval_required: Optional[str] = None
    warranty_years: int = 20
    r_value_required: Optional[float] = None
    cool_roof_required: bool = False
    budget_tier: str = "standard"
    limit: int = 3

class ComponentQueryRequest(BaseModel):
    manufacturer: Optional[str] = None
    category: Optional[str] = None  # membrane, insulation, cover_board, etc.
    system_type: Optional[str] = None
    fm_approval: Optional[str] = None
    cool_roof_eligible: Optional[bool] = None

@router.post("/assemblies/build")
async def build_assembly(request: Request, assembly_req: AssemblyRequest):
    """
    Elena builds a roofing assembly based on requirements

    This endpoint allows Elena to intelligently construct a roofing
    assembly from requirements, selecting compatible components
    and calculating costs.
    """
    try:
        # Get Elena instance from app state
        elena = getattr(request.app.state, 'elena', None)
        if not elena:
            raise HTTPException(status_code=503, detail="Elena AI agent not initialized")

        # Convert request to dict
        requirements = assembly_req.dict()

        # Call Elena's assembly building service
        result = await elena.build_assembly(
            requirements=requirements,
            tenant_id=assembly_req.tenant_id
        )

        if result.get('status') == 'error':
            raise HTTPException(status_code=500, detail=result.get('error', 'Assembly build failed'))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Elena assembly build error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assemblies/recommend")
async def recommend_assemblies(request: Request, rec_req: RecommendationRequest):
    """
    Elena recommends optimal assemblies

    Uses AI-powered scoring to recommend the best assemblies
    for the given requirements, sorted by recommendation score.
    """
    try:
        elena = getattr(request.app.state, 'elena', None)
        if not elena:
            raise HTTPException(status_code=503, detail="Elena AI agent not initialized")

        requirements = rec_req.dict(exclude={'limit'})

        result = await elena.recommend_assemblies(
            requirements=requirements,
            limit=rec_req.limit
        )

        if result.get('status') == 'error':
            raise HTTPException(status_code=500, detail=result.get('error', 'Recommendations failed'))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Elena recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/components/query")
async def query_components(request: Request, query_req: ComponentQueryRequest):
    """
    Elena queries manufacturer components

    Search the manufacturer product catalog based on filters.
    """
    try:
        elena = getattr(request.app.state, 'elena', None)
        if not elena:
            raise HTTPException(status_code=503, detail="Elena AI agent not initialized")

        filters = query_req.dict(exclude_none=True)

        result = await elena.query_components(filters=filters)

        if result.get('status') == 'error':
            raise HTTPException(status_code=500, detail=result.get('error', 'Component query failed'))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Elena component query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workbooks/import")
async def import_workbook(
    request: Request,
    file: UploadFile = File(...),
    tenant_id: str = Form(...)
):
    """
    Elena imports Excel workbook estimate

    Accepts .xlsm files and extracts estimate data to create
    a full estimate in the system.
    """
    try:
        elena = getattr(request.app.state, 'elena', None)
        if not elena:
            raise HTTPException(status_code=503, detail="Elena AI agent not initialized")

        # Validate file type
        if not file.filename.endswith('.xlsm'):
            raise HTTPException(status_code=400, detail="Only .xlsm files are supported")

        # Save uploaded file temporarily
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsm') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Import via Elena
            result = await elena.import_workbook(
                file_path=temp_path,
                tenant_id=tenant_id
            )

            if result.get('status') == 'error':
                raise HTTPException(status_code=500, detail=result.get('error', 'Import failed'))

            return result

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Elena workbook import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def elena_status(request: Request):
    """
    Get Elena's current status and capabilities
    """
    try:
        elena = getattr(request.app.state, 'elena', None)

        if not elena:
            return {
                "status": "not_initialized",
                "agent": "Elena",
                "message": "Elena AI agent is not initialized"
            }

        # Get backend URL
        backend_url = getattr(elena, 'backend_url', 'unknown')

        return {
            "status": "operational",
            "agent": "Elena",
            "agent_type": "estimation",
            "specialization": "roofing_estimation",
            "capabilities": [
                "Intelligent assembly building",
                "AI-powered component recommendations",
                "Assembly recommendation with confidence scoring",
                "Manufacturer component queries",
                "Excel workbook import (.xlsm)"
            ],
            "backend_url": backend_url,
            "integrated_with": "BrainOps Roofing Estimation System",
            "features": {
                "manufacturers": ["Holcim Elevate", "GAF", "Carlisle"],
                "product_categories": ["membrane", "insulation", "cover_board", "base_sheet", "accessory", "flashing"],
                "system_types": ["TPO", "EPDM", "PVC", "ModifiedBitumen", "BuiltUp", "Metal"],
                "fm_approval_ratings": ["1-60", "1-75", "1-90", "1-120", "1-135"],
                "warranty_years": [10, 15, 20, 25, 30]
            }
        }

    except Exception as e:
        logger.error(f"Elena status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def elena_health(request: Request):
    """Quick health check for Elena agent"""
    elena = getattr(request.app.state, 'elena', None)

    return {
        "healthy": elena is not None,
        "agent": "Elena",
        "initialized": elena is not None
    }
