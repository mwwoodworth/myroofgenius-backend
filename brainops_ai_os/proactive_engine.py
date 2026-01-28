"""
BrainOps AI OS - Proactive Intelligence Engine

Provides autonomous intelligence that:
- Detects opportunities before they're obvious
- Predicts problems before they occur
- Suggests actions without being asked
- Monitors for optimal intervention points
- Generates insights from data patterns
"""

import asyncio
import json
import logging
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass, field
import asyncpg
import numpy as np

from ._resilience import ResilientSubsystem

if TYPE_CHECKING:
    from .metacognitive_controller import MetacognitiveController

logger = logging.getLogger(__name__)


class OpportunityType(str, Enum):
    """Types of proactive opportunities"""
    REVENUE = "revenue"
    EFFICIENCY = "efficiency"
    CUSTOMER = "customer"
    RISK = "risk"
    GROWTH = "growth"
    COST_SAVING = "cost_saving"


class PredictionType(str, Enum):
    """Types of predictions"""
    CHURN = "churn"
    REVENUE = "revenue"
    DEMAND = "demand"
    FAILURE = "failure"
    OPPORTUNITY = "opportunity"


@dataclass
class Opportunity:
    """A proactive opportunity"""
    id: str
    type: OpportunityType
    title: str
    description: str
    potential_value: float
    confidence: float
    urgency: float
    recommended_actions: List[Dict[str, Any]]
    context: Dict[str, Any]
    detected_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    acted_upon: bool = False


@dataclass
class Prediction:
    """A proactive prediction"""
    id: str
    type: PredictionType
    target: str
    probability: float
    timeframe: str
    impact: float
    preventive_actions: List[Dict[str, Any]]
    created_at: datetime = field(default_factory=datetime.now)
    verified: Optional[bool] = None


class ProactiveIntelligenceEngine(ResilientSubsystem):
    """
    Proactive Intelligence Engine for BrainOps AI OS

    Provides:
    1. Opportunity detection from business data
    2. Predictive analytics for problems
    3. Autonomous action suggestions
    4. Intervention point optimization
    5. Insight generation
    """

    def __init__(self, controller: "MetacognitiveController"):
        self.controller = controller
        self.db_pool: Optional[asyncpg.Pool] = None

        # Storage
        self.opportunities: Dict[str, Opportunity] = {}
        self.predictions: Dict[str, Prediction] = {}

        # AI client
        self._openai_client = None
        self._openai_key = os.getenv("OPENAI_API_KEY")

        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown = asyncio.Event()

        # Metrics
        self.metrics = {
            "opportunities_detected": 0,
            "predictions_made": 0,
            "actions_suggested": 0,
            "predictions_verified": 0,
        }

    async def initialize(self, db_pool: asyncpg.Pool):
        """Initialize the proactive engine"""
        self.db_pool = db_pool

        if self._openai_key:
            import openai
            self._openai_client = openai.AsyncOpenAI(api_key=self._openai_key)

        await self._initialize_database()
        await self._start_background_processes()

        logger.info("ProactiveIntelligenceEngine initialized")

    async def _initialize_database(self):
        """Create required database tables"""
        await self._db_execute_with_retry('''
            -- Opportunities
            CREATE TABLE IF NOT EXISTS brainops_opportunities (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                opportunity_id VARCHAR(50) UNIQUE NOT NULL,
                opportunity_type VARCHAR(50) NOT NULL,
                title VARCHAR(255),
                description TEXT,
                potential_value FLOAT,
                confidence FLOAT,
                urgency FLOAT,
                recommended_actions JSONB,
                context JSONB,
                expires_at TIMESTAMP,
                acted_upon BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_opportunity_type
                ON brainops_opportunities(opportunity_type);
            CREATE INDEX IF NOT EXISTS idx_opportunity_value
                ON brainops_opportunities(potential_value DESC);

            -- Predictions
            CREATE TABLE IF NOT EXISTS brainops_predictions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                prediction_id VARCHAR(50) UNIQUE NOT NULL,
                prediction_type VARCHAR(50) NOT NULL,
                target VARCHAR(255),
                probability FLOAT,
                timeframe VARCHAR(50),
                impact FLOAT,
                preventive_actions JSONB,
                verified BOOLEAN,
                created_at TIMESTAMP DEFAULT NOW(),
                verified_at TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_prediction_type
                ON brainops_predictions(prediction_type);

            -- Insights
            CREATE TABLE IF NOT EXISTS brainops_insights (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                insight_type VARCHAR(50),
                title VARCHAR(255),
                description TEXT,
                data_source VARCHAR(100),
                confidence FLOAT,
                actionable BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')

    async def _start_background_processes(self):
        """Start background processes"""
        # Opportunity scanning
        self._tasks.append(
            self._create_safe_task(self._opportunity_scan_loop(), name="opportunity_scan")
        )

        # Prediction generation
        self._tasks.append(
            self._create_safe_task(self._prediction_loop(), name="prediction")
        )

        # Insight generation
        self._tasks.append(
            self._create_safe_task(self._insight_generation_loop(), name="insight_generation")
        )

        # Prediction verification
        self._tasks.append(
            self._create_safe_task(self._prediction_verification_loop(), name="prediction_verification")
        )

        logger.info(f"Started {len(self._tasks)} proactive background processes")

    # =========================================================================
    # OPPORTUNITY DETECTION
    # =========================================================================

    async def _opportunity_scan_loop(self):
        """Scan for opportunities"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                await self._scan_for_opportunities()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Opportunity scan error: {e}")
                await asyncio.sleep(300)

    async def _scan_for_opportunities(self):
        """Scan business data for opportunities"""
        # Revenue opportunities - leads not followed up
        unfollowed_leads = await self._db_fetch_with_retry('''
            SELECT id, name, email, score, created_at
            FROM leads
            WHERE status = 'new'
            AND score >= 70
            AND created_at > NOW() - INTERVAL '48 hours'
            AND created_at < NOW() - INTERVAL '4 hours'
        ''')

        for lead in unfollowed_leads:
            await self._create_opportunity(
                OpportunityType.REVENUE,
                f"Hot lead not followed up: {lead['name']}",
                f"Lead with score {lead['score']} hasn't been contacted in over 4 hours",
                potential_value=500,  # Estimated value
                confidence=0.7,
                urgency=0.8,
                context={"lead_id": str(lead['id']), "score": lead['score']},
                actions=[
                    {"action": "call", "target": lead['email']},
                    {"action": "assign", "to": "senior_sales"},
                ]
            )

        # Customer retention - declining activity
        declining_customers = await self._db_fetch_with_retry('''
            SELECT c.id, c.name, c.email,
                   COUNT(DISTINCT j.id) as recent_jobs
            FROM customers c
            LEFT JOIN jobs j ON c.id = j.customer_id
                AND j.created_at > NOW() - INTERVAL '90 days'
            WHERE c.status = 'active'
            AND c.created_at < NOW() - INTERVAL '6 months'
            GROUP BY c.id, c.name, c.email
            HAVING COUNT(DISTINCT j.id) = 0
        ''')

        for customer in declining_customers:
            await self._create_opportunity(
                OpportunityType.CUSTOMER,
                f"Customer re-engagement: {customer['name']}",
                "Long-standing customer with no recent activity",
                potential_value=1000,
                confidence=0.6,
                urgency=0.5,
                context={"customer_id": str(customer['id'])},
                actions=[
                    {"action": "send_email", "template": "reengagement"},
                    {"action": "schedule_call", "purpose": "check_in"},
                ]
            )

        # Cost savings - efficiency opportunities
        # Check for duplicate or redundant operations
        duplicate_operations = await self._db_fetch_with_retry('''
            SELECT COUNT(*) as count, operation_type
            FROM (
                SELECT 'lead_followup' as operation_type, lead_id
                FROM lead_activities
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY lead_id
                HAVING COUNT(*) > 3
            ) duplicates
            GROUP BY operation_type
        ''')

        for op in duplicate_operations:
            if op['count'] > 5:
                await self._create_opportunity(
                    OpportunityType.EFFICIENCY,
                    f"Reduce duplicate {op['operation_type']} operations",
                    f"Found {op['count']} instances of duplicate operations",
                    potential_value=100,
                    confidence=0.8,
                    urgency=0.3,
                    context={"operation_type": op['operation_type'], "count": op['count']},
                    actions=[
                        {"action": "optimize_workflow", "target": op['operation_type']},
                    ]
                )

    async def _create_opportunity(
        self,
        opp_type: OpportunityType,
        title: str,
        description: str,
        potential_value: float,
        confidence: float,
        urgency: float,
        context: Dict[str, Any],
        actions: List[Dict[str, Any]],
        expires_hours: int = 72
    ):
        """Create and store an opportunity"""
        opp_id = str(uuid.uuid4())

        opportunity = Opportunity(
            id=opp_id,
            type=opp_type,
            title=title,
            description=description,
            potential_value=potential_value,
            confidence=confidence,
            urgency=urgency,
            recommended_actions=actions,
            context=context,
            expires_at=datetime.now() + timedelta(hours=expires_hours),
        )

        self.opportunities[opp_id] = opportunity
        self.metrics["opportunities_detected"] += 1
        self.metrics["actions_suggested"] += len(actions)

        # Store in database
        await self._db_execute_with_retry('''
            INSERT INTO brainops_opportunities
            (opportunity_id, opportunity_type, title, description,
             potential_value, confidence, urgency, recommended_actions,
             context, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        ''',
            opp_id, opp_type.value, title, description,
            potential_value, confidence, urgency, json.dumps(actions),
            json.dumps(context), opportunity.expires_at)

        # Notify controller if high value/urgency
        if (potential_value > 500 or urgency > 0.7) and self.controller:
            from .metacognitive_controller import AttentionPriority
            priority = AttentionPriority.URGENT if urgency > 0.7 else AttentionPriority.HIGH
            await self.controller._record_thought({
                "type": "opportunity",
                "opportunity_id": opp_id,
                "title": title,
                "value": potential_value,
                "urgency": urgency,
            }, priority, "proactive_engine")

    # =========================================================================
    # PREDICTION GENERATION
    # =========================================================================

    async def _prediction_loop(self):
        """Generate predictions"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(1800)  # Every 30 minutes

                await self._generate_predictions()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Prediction loop error: {e}")
                await asyncio.sleep(1800)

    async def _generate_predictions(self):
        """Generate predictions from data patterns"""
        # Churn prediction
        at_risk_customers = await self._db_fetch_with_retry('''
            SELECT c.id, c.name,
                   MAX(j.created_at) as last_job,
                   COUNT(DISTINCT j.id) as total_jobs
            FROM customers c
            LEFT JOIN jobs j ON c.id = j.customer_id
            WHERE c.status = 'active'
            GROUP BY c.id, c.name
            HAVING MAX(j.created_at) < NOW() - INTERVAL '180 days'
               OR (COUNT(DISTINCT j.id) > 5 AND MAX(j.created_at) < NOW() - INTERVAL '90 days')
        ''')

        for customer in at_risk_customers:
            await self._create_prediction(
                PredictionType.CHURN,
                target=f"customer:{customer['id']}",
                probability=0.7,
                timeframe="30 days",
                impact=customer['total_jobs'] * 500,
                preventive_actions=[
                    {"action": "outreach_call", "reason": "retention"},
                    {"action": "special_offer", "type": "loyalty_discount"},
                ]
            )

        # Revenue prediction - based on lead pipeline
        pipeline_value = await self._db_fetchval_with_retry('''
            SELECT SUM(
                CASE
                    WHEN score >= 80 THEN estimated_value * 0.8
                    WHEN score >= 60 THEN estimated_value * 0.5
                    WHEN score >= 40 THEN estimated_value * 0.2
                    ELSE estimated_value * 0.05
                END
            )
            FROM leads
            WHERE status NOT IN ('won', 'lost')
            AND estimated_value IS NOT NULL
        ''') or 0

        if pipeline_value > 0:
            await self._create_prediction(
                PredictionType.REVENUE,
                target="pipeline",
                probability=0.6,
                timeframe="30 days",
                impact=float(pipeline_value),
                preventive_actions=[
                    {"action": "focus_high_score_leads"},
                    {"action": "accelerate_follow_ups"},
                ]
            )

    async def _create_prediction(
        self,
        pred_type: PredictionType,
        target: str,
        probability: float,
        timeframe: str,
        impact: float,
        preventive_actions: List[Dict[str, Any]]
    ):
        """Create and store a prediction"""
        pred_id = str(uuid.uuid4())

        prediction = Prediction(
            id=pred_id,
            type=pred_type,
            target=target,
            probability=probability,
            timeframe=timeframe,
            impact=impact,
            preventive_actions=preventive_actions,
        )

        self.predictions[pred_id] = prediction
        self.metrics["predictions_made"] += 1

        await self._db_execute_with_retry('''
            INSERT INTO brainops_predictions
            (prediction_id, prediction_type, target, probability,
             timeframe, impact, preventive_actions)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''',
            pred_id, pred_type.value, target, probability,
            timeframe, impact, json.dumps(preventive_actions))

    # =========================================================================
    # INSIGHT GENERATION
    # =========================================================================

    async def _insight_generation_loop(self):
        """Generate insights from data"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(3600)  # Every hour

                await self._generate_insights()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Insight generation error: {e}")
                await asyncio.sleep(3600)

    async def _generate_insights(self):
        """Generate insights from aggregated data"""
        # Lead source performance
        source_performance = await self._db_fetch_with_retry('''
            SELECT
                source,
                COUNT(*) as total,
                AVG(score) as avg_score,
                SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END)::float /
                    NULLIF(COUNT(*), 0) as conversion_rate
            FROM leads
            WHERE created_at > NOW() - INTERVAL '30 days'
            GROUP BY source
            HAVING COUNT(*) >= 10
        ''')

        for source in source_performance:
            if source['conversion_rate'] and source['conversion_rate'] > 0.3:
                await self._store_insight(
                    "high_converting_source",
                    f"High-converting lead source: {source['source']}",
                    f"Source {source['source']} has {source['conversion_rate']*100:.1f}% conversion rate",
                    "leads",
                    source['conversion_rate']
                )
            elif source['conversion_rate'] and source['conversion_rate'] < 0.05:
                await self._store_insight(
                    "low_converting_source",
                    f"Low-converting lead source: {source['source']}",
                    f"Source {source['source']} has only {source['conversion_rate']*100:.1f}% conversion",
                    "leads",
                    0.8
                )

    async def _store_insight(
        self,
        insight_type: str,
        title: str,
        description: str,
        data_source: str,
        confidence: float
    ):
        """Store an insight"""
        await self._db_execute_with_retry('''
            INSERT INTO brainops_insights
            (insight_type, title, description, data_source, confidence)
            VALUES ($1, $2, $3, $4, $5)
        ''', insight_type, title, description, data_source, confidence)

    # =========================================================================
    # PREDICTION VERIFICATION
    # =========================================================================

    async def _prediction_verification_loop(self):
        """Verify past predictions"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(86400)  # Daily

                await self._verify_predictions()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Prediction verification error: {e}")
                await asyncio.sleep(86400)

    async def _verify_predictions(self):
        """Verify if predictions came true"""
        # Get predictions to verify (older than timeframe)
        predictions = await self._db_fetch_with_retry('''
            SELECT prediction_id, prediction_type, target, probability
            FROM brainops_predictions
            WHERE verified IS NULL
            AND created_at < NOW() - INTERVAL '30 days'
        ''')

        for pred in predictions:
            verified = await self._check_prediction_outcome(
                pred['prediction_type'],
                pred['target']
            )

            await self._db_execute_with_retry('''
                UPDATE brainops_predictions
                SET verified = $2, verified_at = NOW()
                WHERE prediction_id = $1
            ''', pred['prediction_id'], verified)

            self.metrics["predictions_verified"] += 1

    async def _check_prediction_outcome(
        self,
        pred_type: str,
        target: str
    ) -> bool:
        """Check if a prediction came true"""
        # Would implement actual verification logic here
        # For now, return based on type
        return False  # Placeholder

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def get_opportunities(self) -> List[Dict[str, Any]]:
        """Get current opportunities"""
        now = datetime.now()
        return [
            {
                "id": opp.id,
                "type": opp.type.value,
                "title": opp.title,
                "description": opp.description,
                "potential_value": opp.potential_value,
                "confidence": opp.confidence,
                "urgency": opp.urgency,
                "priority": 0 if opp.urgency > 0.8 else (1 if opp.urgency > 0.5 else 2),
                "actions": opp.recommended_actions,
            }
            for opp in self.opportunities.values()
            if not opp.acted_upon and (not opp.expires_at or opp.expires_at > now)
        ]

    async def process_prediction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process prediction request from controller"""
        return {"status": "processed"}

    async def get_health(self) -> Dict[str, Any]:
        """Get proactive engine health"""
        active_tasks = sum(1 for t in self._tasks if not t.done())

        return {
            "status": "healthy" if active_tasks == len(self._tasks) else "degraded",
            "score": active_tasks / len(self._tasks) if self._tasks else 1.0,
            "opportunities_active": len(self.opportunities),
            "predictions_active": len(self.predictions),
            "metrics": self.metrics.copy(),
        }

    async def shutdown(self):
        """Shutdown the proactive engine"""
        self._shutdown.set()

        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("ProactiveIntelligenceEngine shutdown complete")


# Singleton
_proactive_engine: Optional[ProactiveIntelligenceEngine] = None


def get_proactive_engine() -> Optional[ProactiveIntelligenceEngine]:
    """Get the proactive engine instance"""
    return _proactive_engine
