"""
Estimate Generation Workflow
Orchestrates AI agents to create intelligent estimates

Flow:
1. Fetch customer data
2. AI analyzes property
3. Generate pricing (simplified for now)
4. Create estimate record
"""
from typing import TypedDict, Dict, Any
from datetime import datetime
import httpx
import json
import uuid
import asyncpg

from workflows.config import WorkflowConfig
from workflows.state_manager import WorkflowStateManager

class EstimateWorkflowState(TypedDict):
    """Workflow state (preserved across steps)"""
    # Input
    customer_id: str
    property_info: Dict[str, Any]

    # Intermediate data
    customer_data: Dict[str, Any]
    property_analysis: Dict[str, Any]
    pricing_data: Dict[str, Any]

    # Output
    estimate_draft: Dict[str, Any]
    estimate_id: str

    # Metadata
    workflow_id: str
    started_at: str
    errors: list

class EstimateWorkflow:
    """
    Intelligent estimate generation workflow
    Coordinates data fetching, AI analysis, and estimate creation
    """

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.state_manager = WorkflowStateManager(db_pool)
        self.config = WorkflowConfig

    async def execute(
        self,
        customer_id: str,
        property_info: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """Execute the workflow"""

        workflow_id = str(uuid.uuid4())

        # Initial state
        state = {
            "customer_id": customer_id,
            "property_info": property_info,
            "customer_data": {},
            "property_analysis": {},
            "pricing_data": {},
            "estimate_draft": {},
            "estimate_id": "",
            "workflow_id": workflow_id,
            "started_at": datetime.now().isoformat(),
            "errors": []
        }

        # Save initial state
        await self.state_manager.save_state(
            workflow_id=workflow_id,
            workflow_type="estimate_generation",
            state=state,
            user_id=user_id,
            status="running"
        )

        try:
            # Step 1: Fetch customer
            state = await self._fetch_customer(state)

            # Step 2: Analyze property
            state = await self._analyze_property(state)

            # Step 3: Generate pricing
            state = await self._generate_pricing(state)

            # Step 4: Create estimate
            state = await self._create_estimate(state)

            # Mark as completed
            await self.state_manager.save_state(
                workflow_id=workflow_id,
                workflow_type="estimate_generation",
                state=state,
                user_id=user_id,
                status="completed"
            )

            return {
                "workflow_id": workflow_id,
                "estimate_id": state["estimate_id"],
                "estimate": state["estimate_draft"],
                "total_amount": state.get("pricing_data", {}).get("total", 0),
                "ai_confidence": state.get("property_analysis", {}).get("confidence", 0.85),
                "errors": state.get("errors", [])
            }

        except Exception as e:
            # Mark as failed
            state["errors"].append(str(e))
            await self.state_manager.save_state(
                workflow_id=workflow_id,
                workflow_type="estimate_generation",
                state=state,
                user_id=user_id,
                status="failed"
            )

            return {
                "workflow_id": workflow_id,
                "errors": state["errors"],
                "status": "failed"
            }

    async def _fetch_customer(self, state: EstimateWorkflowState) -> EstimateWorkflowState:
        """Step 1: Fetch customer from database"""

        start_time = datetime.now()

        try:
            async with self.db_pool.acquire() as conn:
                customer = await conn.fetchrow("""
                    SELECT * FROM customers WHERE id = $1
                """, state["customer_id"])

                if not customer:
                    raise ValueError(f"Customer not found: {state['customer_id']}")

                state["customer_data"] = dict(customer)

            # Log step execution
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            await self.state_manager.log_step(
                workflow_id=state["workflow_id"],
                step_name="fetch_customer",
                step_result={"customer_id": state["customer_id"]},
                duration_ms=duration_ms
            )

        except Exception as e:
            state["errors"].append(f"fetch_customer: {str(e)}")

        return state

    async def _analyze_property(self, state: EstimateWorkflowState) -> EstimateWorkflowState:
        """Step 2: AI analyzes property for roofing estimate"""

        start_time = datetime.now()

        try:
            llm = self.config.get_llm()

            if llm:
                # Use Claude for property analysis
                prompt = f"""
                Analyze this property for roofing estimate:

                Address: {state['property_info'].get('address', 'Unknown')}
                Property Type: {state['property_info'].get('type', 'residential')}
                Roof Type: {state['property_info'].get('roof_type', 'asphalt shingle')}
                Square Footage: {state['property_info'].get('sq_ft', 0)}
                Stories: {state['property_info'].get('stories', 1)}

                Provide analysis as JSON with these fields:
                - materials_needed (dict with item names and quantities)
                - complexity_level (1-5)
                - recommended_crew_size (number)
                - estimated_labor_hours (number)
                - estimated_materials_cost (number)
                - confidence_score (0.0-1.0)
                """

                analysis_response = await llm.ainvoke(prompt)
                property_analysis = json.loads(analysis_response.content)

            else:
                # Fallback: Rule-based analysis
                sq_ft = state['property_info'].get('sq_ft', 2000)
                property_analysis = {
                    "materials_needed": {
                        "shingles_sq": sq_ft / 100,
                        "underlayment_rolls": sq_ft / 400,
                        "nails_lbs": sq_ft / 50
                    },
                    "complexity_level": 2,
                    "recommended_crew_size": 4,
                    "estimated_labor_hours": sq_ft / 100,
                    "estimated_materials_cost": sq_ft * 2.5,
                    "confidence_score": 0.75
                }

            state["property_analysis"] = property_analysis

            # Log step execution
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            await self.state_manager.log_step(
                workflow_id=state["workflow_id"],
                step_name="analyze_property",
                step_result={"complexity": property_analysis.get("complexity_level", 2)},
                duration_ms=duration_ms
            )

            # Log AI call if LLM was used
            if llm:
                await self.state_manager.log_agent_call(
                    workflow_id=state["workflow_id"],
                    agent_name="claude_property_analyzer",
                    input_data={"property_info": state["property_info"]},
                    output_data=property_analysis,
                    duration_ms=duration_ms,
                    success=True
                )

        except Exception as e:
            state["errors"].append(f"analyze_property: {str(e)}")

        return state

    async def _generate_pricing(self, state: EstimateWorkflowState) -> EstimateWorkflowState:
        """Step 3: Generate pricing"""

        start_time = datetime.now()

        try:
            # Calculate pricing based on property analysis
            materials_cost = state["property_analysis"].get("estimated_materials_cost", 5000)
            labor_hours = state["property_analysis"].get("estimated_labor_hours", 40)
            labor_rate = 75  # $75/hour

            labor_cost = labor_hours * labor_rate
            subtotal = materials_cost + labor_cost
            markup = subtotal * 0.20  # 20% markup
            total = subtotal + markup

            pricing_data = {
                "materials_cost": materials_cost,
                "labor_cost": labor_cost,
                "labor_hours": labor_hours,
                "labor_rate": labor_rate,
                "subtotal": subtotal,
                "markup": markup,
                "total": total,
                "profit_margin": 0.20
            }

            state["pricing_data"] = pricing_data

            # Log step execution
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            await self.state_manager.log_step(
                workflow_id=state["workflow_id"],
                step_name="generate_pricing",
                step_result={"total": total},
                duration_ms=duration_ms
            )

        except Exception as e:
            state["errors"].append(f"generate_pricing: {str(e)}")

        return state

    async def _create_estimate(self, state: EstimateWorkflowState) -> EstimateWorkflowState:
        """Step 4: Create estimate record in database"""

        start_time = datetime.now()

        try:
            estimate_id = str(uuid.uuid4())

            # Generate unique estimate number
            timestamp_part = datetime.now().strftime("%Y%m%d%H%M%S")
            estimate_number = f"EST-AI-{timestamp_part}"

            estimate_data = {
                "id": estimate_id,
                "customer_id": state["customer_id"],
                "estimate_number": estimate_number,
                "property_address": state["property_info"].get("address", ""),
                "total_amount": state["pricing_data"]["total"],
                "labor_cost": state["pricing_data"]["labor_cost"],
                "materials_cost": state["pricing_data"]["materials_cost"],
                "status": "draft",
                "ai_generated": True,
                "ai_confidence": state["property_analysis"].get("confidence_score", 0.85),
                "created_at": datetime.now()
            }

            # Calculate amounts in cents (required for NOT NULL constraints)
            subtotal = state["pricing_data"]["subtotal"]
            total = state["pricing_data"]["total"]
            subtotal_cents = int(subtotal * 100)
            total_cents = int(total * 100)

            # Save to database
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO estimates (
                        id, customer_id, estimate_number, total_amount, labor_cost,
                        materials_cost, status, created_at, tenant_id, estimate_date,
                        subtotal_cents, total_cents
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """, estimate_id, state["customer_id"], estimate_number,
                    estimate_data["total_amount"], estimate_data["labor_cost"],
                    estimate_data["materials_cost"], estimate_data["status"],
                    estimate_data["created_at"],
                    state.get("customer_data", {}).get("tenant_id", "51e728c5-94e8-4ae0-8a0a-6a08d1fb3457"),
                    datetime.now().date(),
                    subtotal_cents, total_cents)

            state["estimate_draft"] = estimate_data
            state["estimate_id"] = estimate_id

            # Log step execution
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            await self.state_manager.log_step(
                workflow_id=state["workflow_id"],
                step_name="create_estimate",
                step_result={"estimate_id": estimate_id},
                duration_ms=duration_ms
            )

        except Exception as e:
            state["errors"].append(f"create_estimate: {str(e)}")

        return state
