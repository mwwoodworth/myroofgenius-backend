"""
Weathercraft ERP Deep Integration
Creates bidirectional awareness and intricate linking between ERP and AI backend

This is NOT just an API wrapper - this creates deep relationships where:
1. ERP actions trigger AI workflows
2. AI insights flow back to ERP in real-time
3. Systems share unified state and memory
4. Deep customer/job/estimate relationships maintained
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncpg
import logging
import httpx

logger = logging.getLogger(__name__)


class WeathercraftERPIntegration:
    """
    Deep integration layer creating intricate bidirectional awareness
    between Weathercraft ERP and AI backend systems
    """

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.erp_url = "https://weathercraft-erp.vercel.app"
        self.backend_url = "https://brainops-backend-prod.onrender.com"

        # CNS for shared memory across systems
        self.cns = None

    async def initialize(self):
        """Initialize integration and establish deep connections"""
        try:
            # Try to import CNS for shared memory
            from cns_service_simplified import BrainOpsCNS

            self.cns = BrainOpsCNS(db_pool=self.db_pool)
            await self.cns.initialize()
            logger.info("✅ CNS connected - shared memory active")
        except Exception as e:
            logger.warning(f"CNS not available: {e}")

        # Create integration tracking tables (V7: guarded by DDL kill-switch)
        try:
            await self._ensure_integration_tables()
        except RuntimeError as e:
            if "BLOCKED_RUNTIME_DDL" in str(e):
                logger.info(
                    "DDL kill-switch active — skipping integration table creation"
                )
            else:
                raise

        logger.info("✅ Weathercraft ERP Integration initialized")

    async def _ensure_integration_tables(self):
        """Create tables for tracking deep integration state.

        V7: All DDL is guarded by the runtime DDL kill-switch.
        In production/staging these tables must already exist via migration.
        """
        from brainops_ai_os._resilience import assert_no_runtime_ddl

        ddl_statements = [
            # Track ERP-Backend sync state
            """CREATE TABLE IF NOT EXISTS erp_backend_sync (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    entity_type VARCHAR(50) NOT NULL,
                    entity_id UUID NOT NULL,
                    erp_state JSONB,
                    backend_state JSONB,
                    ai_enrichments JSONB,
                    last_synced_at TIMESTAMP DEFAULT NOW(),
                    sync_direction VARCHAR(20),
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(entity_type, entity_id)
                )""",
            # Track AI workflow triggers from ERP
            """CREATE TABLE IF NOT EXISTS erp_workflow_triggers (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    erp_entity_type VARCHAR(50) NOT NULL,
                    erp_entity_id UUID NOT NULL,
                    workflow_type VARCHAR(50) NOT NULL,
                    workflow_id UUID,
                    triggered_by_user_id UUID,
                    trigger_context JSONB,
                    workflow_result JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP
                )""",
            # Track AI insights delivered to ERP
            """CREATE TABLE IF NOT EXISTS ai_to_erp_insights (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    insight_type VARCHAR(50) NOT NULL,
                    target_entity_type VARCHAR(50),
                    target_entity_id UUID,
                    insight_data JSONB NOT NULL,
                    confidence_score DECIMAL(3,2),
                    delivered_to_erp BOOLEAN DEFAULT false,
                    viewed_by_user BOOLEAN DEFAULT false,
                    user_action VARCHAR(50),
                    created_at TIMESTAMP DEFAULT NOW(),
                    delivered_at TIMESTAMP,
                    viewed_at TIMESTAMP
                )""",
        ]

        async with self.db_pool.acquire() as conn:
            for ddl in ddl_statements:
                assert_no_runtime_ddl(ddl)
                await conn.execute(ddl)

    # =========================================================================
    # BIDIRECTIONAL CUSTOMER SYNC
    # =========================================================================

    async def sync_customer_to_backend(
        self, customer_id: str, customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        When customer created/updated in ERP → sync to backend → trigger AI enrichment
        """
        try:
            # 1. Store in sync table
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO erp_backend_sync (entity_type, entity_id, erp_state, sync_direction, tenant_id)
                    VALUES ($1, $2, $3, $4, NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
                    ON CONFLICT (entity_type, entity_id) DO UPDATE SET
                        erp_state = $3,
                        last_synced_at = NOW()
                """,
                    "customer",
                    customer_id,
                    customer_data,
                    "erp_to_backend",
                )

            # 2. Trigger AI enrichment workflow
            enrichment = await self._enrich_customer_with_ai(customer_id, customer_data)

            # 3. Store AI insights back to sync table
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE erp_backend_sync
                    SET ai_enrichments = $1,
                        backend_state = $2,
                        last_synced_at = NOW()
                    WHERE entity_type = 'customer' AND entity_id = $3
                """,
                    enrichment,
                    customer_data,
                    customer_id,
                )

            # 4. Store in CNS for shared memory
            if self.cns:
                await self.cns.remember(
                    {
                        "type": "customer",
                        "category": "erp_sync",
                        "title": f'Customer synced: {customer_data.get("name", "Unknown")}',
                        "content": {
                            "customer_id": customer_id,
                            "customer_data": customer_data,
                            "ai_enrichments": enrichment,
                            "source": "weathercraft_erp",
                        },
                        "importance": 0.7,
                        "tags": ["customer", "erp", "sync", "weathercraft"],
                    }
                )

            return {
                "status": "synced",
                "customer_id": customer_id,
                "ai_enrichments": enrichment,
            }

        except Exception as e:
            logger.error(f"Customer sync error: {e}")
            return {"status": "error", "error": str(e)}

    async def _enrich_customer_with_ai(
        self, customer_id: str, customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI enriches customer data with predictions and insights"""

        # Get customer history from database
        async with self.db_pool.acquire() as conn:
            jobs = await conn.fetch(
                """
                SELECT COUNT(*) as job_count,
                       SUM(total_amount) as lifetime_value
                FROM jobs
                WHERE customer_id = $1
            """,
                customer_id,
            )

            estimates = await conn.fetch(
                """
                SELECT COUNT(*) as estimate_count,
                       AVG(total_amount) as avg_estimate
                FROM estimates
                WHERE customer_id = $1
            """,
                customer_id,
            )

        job_data = dict(jobs[0]) if jobs else {}
        estimate_data = dict(estimates[0]) if estimates else {}

        # AI-powered enrichment
        enrichment = {
            "customer_profile": {
                "total_jobs": job_data.get("job_count", 0),
                "lifetime_value": float(job_data.get("lifetime_value") or 0),
                "total_estimates": estimate_data.get("estimate_count", 0),
                "avg_estimate_value": float(estimate_data.get("avg_estimate") or 0),
            },
            "ai_predictions": {
                "churn_risk": self._calculate_churn_risk(job_data),
                "upsell_opportunity": self._calculate_upsell_potential(
                    job_data, estimate_data
                ),
                "next_service_date": self._predict_next_service(job_data),
            },
            "recommendations": self._generate_customer_recommendations(
                customer_data, job_data
            ),
            "enriched_at": datetime.now().isoformat(),
        }

        # Create AI insight for ERP to display
        await self._create_erp_insight(
            insight_type="customer_enrichment",
            target_entity_type="customer",
            target_entity_id=customer_id,
            insight_data=enrichment,
            confidence_score=0.85,
        )

        return enrichment

    def _calculate_churn_risk(self, job_data: Dict) -> str:
        """Predict customer churn risk"""
        job_count = job_data.get("job_count", 0)
        if job_count == 0:
            return "new_customer"
        elif job_count >= 3:
            return "low"
        else:
            return "medium"

    def _calculate_upsell_potential(self, job_data: Dict, estimate_data: Dict) -> str:
        """Predict upsell opportunities"""
        estimate_count = estimate_data.get("estimate_count", 0)
        avg_estimate = estimate_data.get("avg_estimate", 0)

        if estimate_count > 0 and avg_estimate > 10000:
            return "high"
        elif estimate_count > 2:
            return "medium"
        else:
            return "low"

    def _predict_next_service(self, job_data: Dict) -> Optional[str]:
        """Predict when customer will need next service"""
        # Simple rule-based for now (can upgrade to ML model)
        return "2026-04-15"  # Placeholder

    def _generate_customer_recommendations(
        self, customer_data: Dict, job_data: Dict
    ) -> List[str]:
        """Generate actionable recommendations for ERP users"""
        recommendations = []

        if job_data.get("job_count", 0) == 0:
            recommendations.append("Schedule initial consultation")

        if job_data.get("lifetime_value", 0) > 25000:
            recommendations.append("Consider VIP customer program")

        return recommendations

    # =========================================================================
    # ERP-TRIGGERED WORKFLOWS
    # =========================================================================

    async def trigger_estimate_workflow_from_erp(
        self, customer_id: str, property_info: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """
        ERP user clicks 'Generate AI Draft' → triggers workflow → result flows back to ERP
        """
        from workflows.estimate import EstimateWorkflow

        try:
            # 1. Record trigger
            trigger_id = None
            async with self.db_pool.acquire() as conn:
                trigger_record = await conn.fetchrow(
                    """
                    INSERT INTO erp_workflow_triggers (
                        erp_entity_type, erp_entity_id, workflow_type,
                        triggered_by_user_id, trigger_context, tenant_id
                    )
                    VALUES ($1, $2, $3, $4, $5, NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
                    RETURNING id
                """,
                    "estimate",
                    customer_id,
                    "estimate_generation",
                    user_id,
                    property_info,
                )
                trigger_id = trigger_record["id"]

            # 2. Execute workflow
            workflow = EstimateWorkflow(self.db_pool)
            result = await workflow.execute(
                customer_id=customer_id, property_info=property_info, user_id=user_id
            )

            # 3. Update trigger record with result
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE erp_workflow_triggers
                    SET workflow_id = $1,
                        workflow_result = $2,
                        completed_at = NOW()
                    WHERE id = $3
                """,
                    result.get("workflow_id"),
                    result,
                    trigger_id,
                )

            # 4. Create insight for ERP to display
            await self._create_erp_insight(
                insight_type="ai_estimate_draft",
                target_entity_type="estimate",
                target_entity_id=result.get("estimate_id"),
                insight_data={
                    "estimate": result.get("estimate"),
                    "total_amount": result.get("total_amount"),
                    "ai_confidence": result.get("ai_confidence"),
                    "workflow_id": result.get("workflow_id"),
                    "message": "AI-generated draft ready for review",
                },
                confidence_score=result.get("ai_confidence", 0.85),
            )

            # 5. Store in CNS
            if self.cns:
                await self.cns.remember(
                    {
                        "type": "workflow",
                        "category": "estimate_generation",
                        "title": f'AI Estimate Draft: ${result.get("total_amount", 0):,.0f}',
                        "content": {
                            "workflow_id": result.get("workflow_id"),
                            "estimate_id": result.get("estimate_id"),
                            "customer_id": customer_id,
                            "total_amount": result.get("total_amount"),
                            "triggered_from": "weathercraft_erp",
                            "user_id": user_id,
                        },
                        "importance": 0.8,
                        "tags": ["estimate", "workflow", "erp", "ai_draft"],
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Workflow trigger error: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # AI INSIGHTS TO ERP
    # =========================================================================

    async def _create_erp_insight(
        self,
        insight_type: str,
        target_entity_type: str,
        target_entity_id: str,
        insight_data: Dict[str, Any],
        confidence_score: float,
    ):
        """Create AI insight that will be delivered to ERP UI"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ai_to_erp_insights (
                    insight_type, target_entity_type, target_entity_id,
                    insight_data, confidence_score, tenant_id
                )
                VALUES ($1, $2, $3, $4, $5, NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
            """,
                insight_type,
                target_entity_type,
                target_entity_id,
                insight_data,
                confidence_score,
            )

    async def get_erp_insights(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        unviewed_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get AI insights for ERP to display"""
        query = """
            SELECT * FROM ai_to_erp_insights
            WHERE 1=1
        """
        params = []
        param_count = 1

        if entity_type:
            query += f" AND target_entity_type = ${param_count}"
            params.append(entity_type)
            param_count += 1

        if entity_id:
            query += f" AND target_entity_id = ${param_count}"
            params.append(entity_id)
            param_count += 1

        if unviewed_only:
            query += " AND viewed_by_user = false"

        query += " ORDER BY created_at DESC"

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def mark_insight_viewed(
        self, insight_id: str, user_action: Optional[str] = None
    ):
        """Mark AI insight as viewed by ERP user"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE ai_to_erp_insights
                SET viewed_by_user = true,
                    viewed_at = NOW(),
                    user_action = $2
                WHERE id = $1
            """,
                insight_id,
                user_action,
            )

    # =========================================================================
    # DEEP RELATIONSHIP QUERIES
    # =========================================================================

    async def get_unified_customer_view(self, customer_id: str) -> Dict[str, Any]:
        """
        Get complete unified view of customer across ERP and AI systems
        """
        async with self.db_pool.acquire() as conn:
            # Get customer base data
            customer = await conn.fetchrow(
                """
                SELECT * FROM customers WHERE id = $1
            """,
                customer_id,
            )

            # Get sync state
            sync_state = await conn.fetchrow(
                """
                SELECT * FROM erp_backend_sync
                WHERE entity_type = 'customer' AND entity_id = $1
            """,
                customer_id,
            )

            # Get AI insights
            insights = await conn.fetch(
                """
                SELECT * FROM ai_to_erp_insights
                WHERE target_entity_type = 'customer'
                  AND target_entity_id = $1
                ORDER BY created_at DESC
                LIMIT 10
            """,
                customer_id,
            )

            # Get workflow history
            workflows = await conn.fetch(
                """
                SELECT * FROM erp_workflow_triggers
                WHERE erp_entity_id = $1
                ORDER BY created_at DESC
                LIMIT 20
            """,
                customer_id,
            )

            # Get jobs and estimates
            jobs = await conn.fetch(
                """
                SELECT * FROM jobs WHERE customer_id = $1 ORDER BY created_at DESC
            """,
                customer_id,
            )

            estimates = await conn.fetch(
                """
                SELECT * FROM estimates WHERE customer_id = $1 ORDER BY created_at DESC
            """,
                customer_id,
            )

        return {
            "customer": dict(customer) if customer else None,
            "ai_enrichments": dict(sync_state)["ai_enrichments"] if sync_state else {},
            "ai_insights": [dict(row) for row in insights],
            "workflow_history": [dict(row) for row in workflows],
            "jobs": [dict(row) for row in jobs],
            "estimates": [dict(row) for row in estimates],
            "relationship_strength": self._calculate_relationship_strength(
                jobs, estimates
            ),
            "unified_at": datetime.now().isoformat(),
        }

    def _calculate_relationship_strength(self, jobs: List, estimates: List) -> str:
        """Calculate customer relationship strength"""
        job_count = len(jobs)
        estimate_count = len(estimates)

        if job_count >= 5:
            return "strong"
        elif job_count >= 2:
            return "moderate"
        elif estimate_count > 0:
            return "developing"
        else:
            return "new"
