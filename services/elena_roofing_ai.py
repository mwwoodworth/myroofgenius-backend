"""
Elena - Roofing Estimation AI Agent
Enhanced with enterprise roofing capabilities
"""

import asyncpg
import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ElenaRoofingAI:
    """
    Elena - The Roofing Estimation AI Agent

    Capabilities:
    - Intelligent assembly building based on requirements
    - AI-powered component recommendations
    - Assembly recommendation with confidence scoring
    - Integration with roofing estimation backend
    """

    def __init__(self, db_pool: asyncpg.Pool, backend_url: str = "http://localhost:8000"):
        self.db_pool = db_pool
        self.backend_url = backend_url
        self.name = "Elena"
        self.agent_type = "estimation"
        self.specialization = "roofing_estimation"

    async def build_assembly(
        self,
        requirements: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a roofing assembly based on requirements

        Args:
            requirements: Dict containing:
                - system_type: TPO, EPDM, PVC, etc.
                - deck_type: concrete, steel, wood, etc.
                - wind_zone_psf: Wind uplift in PSF
                - fm_approval_required: 1-60, 1-75, 1-90, 1-120, 1-135
                - warranty_years: 10, 15, 20, 25, 30
                - r_value_required: Thermal resistance
                - cool_roof_required: Boolean
                - budget_tier: economy, standard, premium
                - preferred_manufacturer: Optional
            tenant_id: Optional tenant ID for caching

        Returns:
            Dict with assembly details and components
        """
        try:
            # Call backend roofing estimation API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.backend_url}/api/v1/roofing/assemblies/build",
                    json=requirements
                )

                if response.status_code == 200:
                    assembly_data = response.json()

                    # Log the assembly build
                    await self._log_assembly_build(
                        requirements=requirements,
                        assembly=assembly_data,
                        tenant_id=tenant_id
                    )

                    return {
                        "status": "success",
                        "agent": "Elena",
                        "assembly": assembly_data,
                        "confidence": self._calculate_confidence(assembly_data),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.error(f"Assembly build failed: HTTP {response.status_code}")
                    return {
                        "status": "error",
                        "error": f"Backend returned HTTP {response.status_code}",
                        "timestamp": datetime.now().isoformat()
                    }

        except Exception as e:
            logger.error(f"Elena assembly build error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def recommend_assemblies(
        self,
        requirements: Dict[str, Any],
        limit: int = 3
    ) -> Dict[str, Any]:
        """
        Get AI-powered assembly recommendations

        Args:
            requirements: Same as build_assembly
            limit: Number of recommendations to return

        Returns:
            Dict with recommended assemblies sorted by score
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.backend_url}/api/v1/roofing/assemblies/recommend",
                    json={**requirements, "limit": limit}
                )

                if response.status_code == 200:
                    recommendations = response.json()

                    return {
                        "status": "success",
                        "agent": "Elena",
                        "recommendations": recommendations.get("recommendations", []),
                        "analysis": self._analyze_recommendations(recommendations),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.error(f"Recommendations failed: HTTP {response.status_code}")
                    return {
                        "status": "error",
                        "error": f"Backend returned HTTP {response.status_code}",
                        "timestamp": datetime.now().isoformat()
                    }

        except Exception as e:
            logger.error(f"Elena recommendations error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def query_components(
        self,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Query manufacturer components

        Args:
            filters: Dict containing:
                - manufacturer: Optional manufacturer name
                - category: membrane, insulation, cover_board, etc.
                - system_type: TPO, EPDM, PVC, etc.
                - fm_approval: FM approval rating
                - cool_roof_eligible: Boolean

        Returns:
            Dict with matching components
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.backend_url}/api/v1/roofing/components",
                    params=filters
                )

                if response.status_code == 200:
                    components_data = response.json()

                    return {
                        "status": "success",
                        "agent": "Elena",
                        "components": components_data.get("components", []),
                        "count": len(components_data.get("components", [])),
                        "filters_applied": filters,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.error(f"Component query failed: HTTP {response.status_code}")
                    return {
                        "status": "error",
                        "error": f"Backend returned HTTP {response.status_code}",
                        "timestamp": datetime.now().isoformat()
                    }

        except Exception as e:
            logger.error(f"Elena component query error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def import_workbook(
        self,
        file_path: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Import Excel workbook estimate

        Args:
            file_path: Path to .xlsm file
            tenant_id: Tenant ID

        Returns:
            Dict with import status and created estimate ID
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.split('/')[-1], f, 'application/vnd.ms-excel.sheet.macroEnabled.12')}

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.backend_url}/api/v1/roofing/workbooks/import",
                        files=files,
                        data={'tenant_id': tenant_id}
                    )

                    if response.status_code == 200:
                        import_data = response.json()

                        return {
                            "status": "success",
                            "agent": "Elena",
                            "import_result": import_data,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {
                            "status": "error",
                            "error": f"Import failed: HTTP {response.status_code}",
                            "timestamp": datetime.now().isoformat()
                        }

        except Exception as e:
            logger.error(f"Elena workbook import error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _log_assembly_build(
        self,
        requirements: Dict[str, Any],
        assembly: Dict[str, Any],
        tenant_id: Optional[str]
    ):
        """Log assembly build to database"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO ai_agent_activity_tracking (
                        agent_id,
                        action_type,
                        action_details,
                        result,
                        tenant_id,
                        created_at
                    )
                    SELECT
                        id,
                        'roofing_assembly_build',
                        $1::jsonb,
                        $2::jsonb,
                        $3,
                        NOW()
                    FROM ai_agents
                    WHERE name = 'Elena'
                    LIMIT 1
                """, json.dumps(requirements), json.dumps(assembly), tenant_id)
        except Exception as e:
            logger.warning(f"Failed to log assembly build: {e}")

    def _calculate_confidence(self, assembly: Dict[str, Any]) -> float:
        """
        Calculate confidence score for an assembly

        Factors:
        - FM approval match: +20
        - Warranty match: +15
        - R-value match: +15
        - Cool roof compliance: +10
        - Budget tier match: +10
        - Component availability: +15
        - Installation complexity: +15
        """
        confidence = 50.0  # Base confidence

        # FM approval match
        if assembly.get("achieves_fm_approval") == assembly.get("requirements", {}).get("fm_approval_required"):
            confidence += 20

        # Warranty match
        if assembly.get("achieves_warranty_years", 0) >= assembly.get("requirements", {}).get("warranty_years", 0):
            confidence += 15

        # R-value match
        required_r = assembly.get("requirements", {}).get("r_value_required", 0)
        achieved_r = assembly.get("achieves_r_value", 0)
        if required_r > 0 and achieved_r >= required_r:
            confidence += 15

        # Cool roof compliance
        if assembly.get("is_cool_roof_compliant") and assembly.get("requirements", {}).get("cool_roof_required"):
            confidence += 10

        # Component count (more components = more complexity, lower confidence)
        component_count = len(assembly.get("components", []))
        if component_count <= 5:
            confidence += 15
        elif component_count <= 8:
            confidence += 10
        elif component_count <= 12:
            confidence += 5

        return min(100.0, confidence)

    def _analyze_recommendations(self, recommendations_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze recommendations and provide insights
        """
        recommendations = recommendations_data.get("recommendations", [])

        if not recommendations:
            return {"insight": "No suitable assemblies found for the given requirements"}

        top_rec = recommendations[0]

        analysis = {
            "top_choice": top_rec.get("assembly_name"),
            "confidence_score": top_rec.get("ai_recommendation_score"),
            "total_cost_sqft": top_rec.get("total_cost_sqft"),
            "key_advantages": []
        }

        # Identify key advantages
        if top_rec.get("achieves_fm_approval"):
            analysis["key_advantages"].append(f"Meets FM {top_rec['achieves_fm_approval']} approval")

        if top_rec.get("is_cool_roof_compliant"):
            analysis["key_advantages"].append("Cool roof compliant - energy savings")

        if top_rec.get("achieves_warranty_years", 0) >= 25:
            analysis["key_advantages"].append(f"{top_rec['achieves_warranty_years']}-year warranty - premium protection")

        if top_rec.get("achieves_r_value", 0) >= 20:
            analysis["key_advantages"].append(f"High R-value ({top_rec['achieves_r_value']}) - excellent insulation")

        # Cost comparison
        if len(recommendations) > 1:
            costs = [r.get("total_cost_sqft", 0) for r in recommendations]
            avg_cost = sum(costs) / len(costs)
            if top_rec.get("total_cost_sqft", 0) < avg_cost:
                analysis["cost_note"] = "Below average cost - good value"
            elif top_rec.get("total_cost_sqft", 0) > avg_cost * 1.2:
                analysis["cost_note"] = "Premium pricing - highest quality components"
            else:
                analysis["cost_note"] = "Market-rate pricing"

        return analysis


# Global instance
_elena_instance: Optional[ElenaRoofingAI] = None

async def initialize_elena(db_pool: asyncpg.Pool, backend_url: str = "http://localhost:8000"):
    """Initialize global Elena instance"""
    global _elena_instance
    _elena_instance = ElenaRoofingAI(db_pool, backend_url)
    logger.info("🏗️ Elena Roofing AI initialized")
    return _elena_instance

def get_elena() -> ElenaRoofingAI:
    """Get global Elena instance"""
    global _elena_instance
    if _elena_instance is None:
        raise Exception("Elena not initialized - call initialize_elena() first")
    return _elena_instance
