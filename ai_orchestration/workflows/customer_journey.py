"""
Customer Journey Workflow - LangGraph Implementation
Orchestrates the complete customer lifecycle from lead to revenue.
"""

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
import asyncio
import asyncpg
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Database connection - loaded from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

class CustomerState(TypedDict):
    """State for customer journey workflow"""
    customer_id: str
    stage: str  # lead, qualified, converted, active, at_risk, churned
    score: int
    interactions: List[Dict]
    revenue: float
    next_action: str
    metadata: Dict[str, Any]

class CustomerJourneyWorkflow:
    """
    Orchestrates the complete customer lifecycle using LangGraph
    """
    
    def __init__(self):
        self.graph = self._build_graph()
        self.pool = None
        
    def _build_graph(self) -> StateGraph:
        """Build the customer journey graph"""
        workflow = StateGraph(CustomerState)
        
        # Define nodes
        workflow.add_node("lead_capture", self.lead_capture)
        workflow.add_node("lead_scoring", self.lead_scoring)
        workflow.add_node("lead_nurturing", self.lead_nurturing)
        workflow.add_node("conversion", self.conversion)
        workflow.add_node("onboarding", self.onboarding)
        workflow.add_node("engagement", self.engagement)
        workflow.add_node("retention", self.retention)
        workflow.add_node("upsell", self.upsell)
        workflow.add_node("churn_prevention", self.churn_prevention)
        workflow.add_node("reactivation", self.reactivation)
        
        # Define edges
        workflow.add_edge("lead_capture", "lead_scoring")
        workflow.add_conditional_edges(
            "lead_scoring",
            self.route_after_scoring,
            {
                "nurture": "lead_nurturing",
                "convert": "conversion",
                "disqualify": END
            }
        )
        workflow.add_edge("lead_nurturing", "lead_scoring")
        workflow.add_edge("conversion", "onboarding")
        workflow.add_edge("onboarding", "engagement")
        workflow.add_conditional_edges(
            "engagement",
            self.route_after_engagement,
            {
                "upsell": "upsell",
                "retain": "retention",
                "at_risk": "churn_prevention"
            }
        )
        workflow.add_edge("retention", "engagement")
        workflow.add_edge("upsell", "engagement")
        workflow.add_conditional_edges(
            "churn_prevention",
            self.route_after_churn_prevention,
            {
                "saved": "retention",
                "lost": "reactivation"
            }
        )
        workflow.add_edge("reactivation", END)
        
        # Set entry point
        workflow.set_entry_point("lead_capture")
        
        return workflow.compile()
    
    async def connect_db(self):
        """Connect to database"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    
    async def lead_capture(self, state: CustomerState) -> CustomerState:
        """Capture and initialize lead"""
        await self.connect_db()
        
        # Record lead capture
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_funnel_tracking (user_id, funnel_stage, metadata)
                VALUES ($1::UUID, $2, $3)
            """, state["customer_id"], "lead_capture", json.dumps(state.get("metadata", {})))
        
        state["stage"] = "lead"
        state["interactions"].append({
            "type": "lead_captured",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Lead captured: {state['customer_id']}")
        return state
    
    async def lead_scoring(self, state: CustomerState) -> CustomerState:
        """Score the lead based on various factors"""
        await self.connect_db()
        
        score = 0
        
        # Score based on source
        source = state.get("metadata", {}).get("source", "")
        if source == "referral":
            score += 30
        elif source == "google_ads":
            score += 20
        elif source == "website":
            score += 15
        
        # Score based on interactions
        interaction_count = len(state["interactions"])
        score += min(interaction_count * 5, 25)
        
        # Score based on profile completeness
        if state.get("metadata", {}).get("phone"):
            score += 10
        if state.get("metadata", {}).get("company"):
            score += 15
        
        # Check for high-value indicators
        if state.get("metadata", {}).get("budget", 0) > 10000:
            score += 20
        
        state["score"] = score
        
        # Update database
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE leads SET score = $1 WHERE id = $2::UUID
            """, score, state["customer_id"])
        
        logger.info(f"Lead scored: {state['customer_id']} - Score: {score}")
        return state
    
    def route_after_scoring(self, state: CustomerState) -> str:
        """Route based on lead score"""
        if state["score"] >= 70:
            return "convert"
        elif state["score"] >= 30:
            return "nurture"
        else:
            return "disqualify"
    
    async def lead_nurturing(self, state: CustomerState) -> CustomerState:
        """Nurture the lead with targeted content"""
        await self.connect_db()
        
        # Record nurturing activity
        nurture_actions = [
            "sent_educational_email",
            "shared_case_study",
            "invited_to_webinar",
            "sent_pricing_guide"
        ]
        
        # Pick next nurture action
        action_index = len(state["interactions"]) % len(nurture_actions)
        action = nurture_actions[action_index]
        
        state["interactions"].append({
            "type": action,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Increase score slightly for engagement
        state["score"] += 5
        
        logger.info(f"Lead nurtured: {state['customer_id']} - Action: {action}")
        return state
    
    async def conversion(self, state: CustomerState) -> CustomerState:
        """Convert lead to customer"""
        await self.connect_db()
        
        async with self.pool.acquire() as conn:
            # Update lead status
            await conn.execute("""
                UPDATE leads 
                SET status = 'converted', converted_at = NOW()
                WHERE id = $1::UUID
            """, state["customer_id"])
            
            # Record conversion
            await conn.execute("""
                UPDATE user_funnel_tracking 
                SET conversion = true, exited_at = NOW()
                WHERE user_id = $1::UUID AND funnel_stage = 'lead_nurturing'
            """, state["customer_id"])
        
        state["stage"] = "converted"
        state["interactions"].append({
            "type": "converted_to_customer",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Lead converted: {state['customer_id']}")
        return state
    
    async def onboarding(self, state: CustomerState) -> CustomerState:
        """Onboard new customer"""
        state["stage"] = "active"
        state["interactions"].append({
            "type": "onboarding_completed",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Set up initial subscription
        if not state.get("revenue"):
            state["revenue"] = 97.00  # Basic plan
        
        logger.info(f"Customer onboarded: {state['customer_id']}")
        return state
    
    async def engagement(self, state: CustomerState) -> CustomerState:
        """Monitor and improve customer engagement"""
        await self.connect_db()
        
        # Calculate engagement score
        async with self.pool.acquire() as conn:
            activity = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as session_count,
                    MAX(created_at) as last_active
                FROM user_sessions
                WHERE user_id = $1::UUID
                AND created_at > NOW() - INTERVAL '30 days'
            """, state["customer_id"])
            
            if activity:
                session_count = activity["session_count"]
                if session_count > 20:
                    state["next_action"] = "upsell"
                elif session_count < 5:
                    state["next_action"] = "at_risk"
                else:
                    state["next_action"] = "retain"
        
        logger.info(f"Engagement checked: {state['customer_id']} - Next: {state['next_action']}")
        return state
    
    def route_after_engagement(self, state: CustomerState) -> str:
        """Route based on engagement level"""
        return state.get("next_action", "retain")
    
    async def retention(self, state: CustomerState) -> CustomerState:
        """Retain engaged customers"""
        state["interactions"].append({
            "type": "retention_campaign",
            "timestamp": datetime.utcnow().isoformat(),
            "action": "sent_loyalty_reward"
        })
        
        logger.info(f"Retention action: {state['customer_id']}")
        return state
    
    async def upsell(self, state: CustomerState) -> CustomerState:
        """Upsell to higher tier"""
        current_revenue = state.get("revenue", 97)
        
        if current_revenue < 197:
            new_revenue = 197  # Professional plan
            upsell_type = "professional"
        else:
            new_revenue = 497  # Enterprise plan
            upsell_type = "enterprise"
        
        state["revenue"] = new_revenue
        state["interactions"].append({
            "type": "upsell_successful",
            "plan": upsell_type,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Upsell successful: {state['customer_id']} - New MRR: ${new_revenue}")
        return state
    
    async def churn_prevention(self, state: CustomerState) -> CustomerState:
        """Prevent customer churn"""
        prevention_actions = [
            "personal_outreach",
            "special_discount",
            "feature_training",
            "success_manager_assigned"
        ]
        
        # Try prevention action
        action = prevention_actions[0]  # Would be more sophisticated in production
        
        state["interactions"].append({
            "type": "churn_prevention",
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Simulate success rate
        import random
        if random.random() > 0.3:  # 70% success rate
            state["next_action"] = "saved"
            logger.info(f"Churn prevented: {state['customer_id']}")
        else:
            state["next_action"] = "lost"
            logger.info(f"Customer churned: {state['customer_id']}")
        
        return state
    
    def route_after_churn_prevention(self, state: CustomerState) -> str:
        """Route based on churn prevention outcome"""
        return state.get("next_action", "lost")
    
    async def reactivation(self, state: CustomerState) -> CustomerState:
        """Attempt to reactivate churned customer"""
        state["stage"] = "reactivation"
        state["interactions"].append({
            "type": "reactivation_campaign",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Reactivation attempted: {state['customer_id']}")
        return state
    
    async def run(self, customer_id: str, initial_metadata: Dict = None) -> CustomerState:
        """Run the complete customer journey workflow"""
        initial_state = CustomerState(
            customer_id=customer_id,
            stage="new",
            score=0,
            interactions=[],
            revenue=0.0,
            next_action="",
            metadata=initial_metadata or {}
        )
        
        # Execute the workflow
        final_state = await self.graph.ainvoke(initial_state)
        
        # Store workflow execution
        await self.connect_db()
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO workflow_executions (workflow_name, execution_data, status)
                VALUES ($1, $2, $3)
            """, "customer_journey", json.dumps(final_state), "completed")
        
        return final_state

# Create singleton instance
customer_journey_workflow = CustomerJourneyWorkflow()