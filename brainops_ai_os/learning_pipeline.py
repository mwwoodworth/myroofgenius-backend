"""
BrainOps AI OS - Closed-Loop Learning Pipeline

Implements continuous learning from production data:
- Outcome tracking and feedback loops
- Pattern recognition and extraction
- Knowledge synthesis
- Model improvement suggestions
- A/B testing and experimentation
- Performance regression detection
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import asyncpg
import numpy as np

from ._resilience import ResilientSubsystem

if TYPE_CHECKING:
    from .metacognitive_controller import MetacognitiveController

logger = logging.getLogger(__name__)


class LearningType(str, Enum):
    """Types of learning"""
    REINFORCEMENT = "reinforcement"   # Learning from outcomes
    PATTERN = "pattern"               # Pattern recognition
    CORRECTION = "correction"         # Error correction
    OPTIMIZATION = "optimization"     # Performance optimization
    TRANSFER = "transfer"             # Cross-domain learning


class PatternCategory(str, Enum):
    """Categories of patterns"""
    BEHAVIORAL = "behavioral"
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    ANOMALOUS = "anomalous"
    SUCCESSFUL = "successful"


@dataclass
class LearningOutcome:
    """Tracked outcome for learning"""
    id: str
    decision_id: str
    action_type: str
    expected_result: Dict[str, Any]
    actual_result: Dict[str, Any]
    success: bool
    feedback_score: float  # -1 to 1
    context: Dict[str, Any]
    learned_at: datetime = field(default_factory=datetime.now)


@dataclass
class Pattern:
    """A learned pattern"""
    id: str
    category: PatternCategory
    description: str
    conditions: List[Dict[str, Any]]
    outcomes: List[Dict[str, Any]]
    confidence: float
    occurrence_count: int
    last_seen: datetime
    created_at: datetime = field(default_factory=datetime.now)


class LearningPipeline(ResilientSubsystem):
    """
    Closed-Loop Learning Pipeline for BrainOps AI OS

    Provides:
    1. Outcome tracking from all decisions
    2. Pattern extraction and recognition
    3. Knowledge synthesis from patterns
    4. Continuous improvement recommendations
    5. Performance regression detection
    """

    def __init__(self, controller: "MetacognitiveController"):
        self.controller = controller
        self.db_pool: Optional[asyncpg.Pool] = None

        # Learning storage
        self.outcomes: Dict[str, LearningOutcome] = {}
        self.patterns: Dict[str, Pattern] = {}

        # Pattern detection buffers
        self.recent_outcomes: List[LearningOutcome] = []
        self.outcome_buffer_size = 1000

        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown = asyncio.Event()

        # Metrics
        self.metrics = {
            "outcomes_tracked": 0,
            "patterns_discovered": 0,
            "learnings_applied": 0,
            "improvements_suggested": 0,
        }

    async def initialize(self, db_pool: asyncpg.Pool):
        """Initialize the learning pipeline"""
        self.db_pool = db_pool

        # Create database tables
        try:
            await self._initialize_database()
        except Exception as e:
            if "permission denied" in str(e).lower():
                pass
            else:
                raise

        # Load existing patterns
        await self._load_patterns()

        # Start background processes
        await self._start_background_processes()

        logger.info(f"LearningPipeline initialized with {len(self.patterns)} patterns")

    async def _initialize_database(self):
        """Create required database tables"""
        await self._db_execute_with_retry('''
            -- Learning outcomes
            CREATE TABLE IF NOT EXISTS brainops_learning_outcomes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                outcome_id VARCHAR(50) UNIQUE NOT NULL,
                decision_id VARCHAR(50),
                action_type VARCHAR(100),
                expected_result JSONB,
                actual_result JSONB,
                success BOOLEAN,
                feedback_score FLOAT,
                context JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_outcome_decision
                ON brainops_learning_outcomes(decision_id);
            CREATE INDEX IF NOT EXISTS idx_outcome_success
                ON brainops_learning_outcomes(success);
            CREATE INDEX IF NOT EXISTS idx_outcome_time
                ON brainops_learning_outcomes(created_at DESC);

            -- Learned patterns
            CREATE TABLE IF NOT EXISTS brainops_learned_patterns (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                pattern_id VARCHAR(50) UNIQUE NOT NULL,
                category VARCHAR(50) NOT NULL,
                description TEXT,
                conditions JSONB,
                outcomes JSONB,
                confidence FLOAT DEFAULT 0.5,
                occurrence_count INT DEFAULT 1,
                last_seen TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_pattern_category
                ON brainops_learned_patterns(category);
            CREATE INDEX IF NOT EXISTS idx_pattern_confidence
                ON brainops_learned_patterns(confidence DESC);

            -- Learning suggestions
            CREATE TABLE IF NOT EXISTS brainops_learning_suggestions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                suggestion_type VARCHAR(50),
                description TEXT,
                evidence JSONB,
                priority FLOAT DEFAULT 0.5,
                implemented BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );

            -- Experiments/A/B tests
            CREATE TABLE IF NOT EXISTS brainops_experiments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                experiment_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255),
                description TEXT,
                variants JSONB,
                metrics JSONB,
                status VARCHAR(20) DEFAULT 'running',
                winner VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP
            );
        ''')

    async def _load_patterns(self):
        """Load existing patterns from database"""
        rows = await self._db_fetch_with_retry('''
            SELECT pattern_id, category, description, conditions, outcomes,
                   confidence, occurrence_count, last_seen, created_at
            FROM brainops_learned_patterns
            WHERE confidence > 0.3
        ''')

        for row in rows:
            pattern = Pattern(
                id=row['pattern_id'],
                category=PatternCategory(row['category']),
                description=row['description'] or "",
                conditions=row['conditions'] or [],
                outcomes=row['outcomes'] or [],
                confidence=row['confidence'],
                occurrence_count=row['occurrence_count'],
                last_seen=row['last_seen'],
                created_at=row['created_at'],
            )
            self.patterns[pattern.id] = pattern

    async def _start_background_processes(self):
        """Start background processes"""
        # Pattern detection
        self._tasks.append(
            self._create_safe_task(self._pattern_detection_loop(), name="pattern_detection")
        )

        # Knowledge synthesis
        self._tasks.append(
            self._create_safe_task(self._knowledge_synthesis_loop(), name="knowledge_synthesis")
        )

        # Performance monitoring
        self._tasks.append(
            self._create_safe_task(self._performance_monitoring_loop(), name="performance_monitoring")
        )

        logger.info(f"Started {len(self._tasks)} learning background processes")

    # =========================================================================
    # OUTCOME TRACKING
    # =========================================================================

    async def track_outcome(
        self,
        decision_id: str,
        action_type: str,
        expected_result: Dict[str, Any],
        actual_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track an outcome for learning"""
        outcome_id = str(uuid.uuid4())

        # Calculate success and feedback score
        success = self._evaluate_success(expected_result, actual_result)
        feedback_score = self._calculate_feedback_score(expected_result, actual_result)

        outcome = LearningOutcome(
            id=outcome_id,
            decision_id=decision_id,
            action_type=action_type,
            expected_result=expected_result,
            actual_result=actual_result,
            success=success,
            feedback_score=feedback_score,
            context=context or {},
        )

        self.outcomes[outcome_id] = outcome
        self.recent_outcomes.append(outcome)

        # Keep buffer size limited
        if len(self.recent_outcomes) > self.outcome_buffer_size:
            self.recent_outcomes = self.recent_outcomes[-self.outcome_buffer_size:]

        self.metrics["outcomes_tracked"] += 1

        # Store in database
        await self._db_execute_with_retry('''
            INSERT INTO brainops_learning_outcomes
            (outcome_id, decision_id, action_type, expected_result,
             actual_result, success, feedback_score, context)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ''',
            outcome_id, decision_id, action_type,
            json.dumps(expected_result), json.dumps(actual_result),
            success, feedback_score, json.dumps(context or {}))

        return outcome_id

    def _evaluate_success(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> bool:
        """Evaluate if outcome was successful"""
        # Check for explicit success indicators
        if 'success' in actual:
            return actual['success']

        if 'error' in actual:
            return False

        # Compare key metrics if present
        for key in ['score', 'value', 'result']:
            if key in expected and key in actual:
                exp_val = expected[key]
                act_val = actual[key]
                if isinstance(exp_val, (int, float)) and isinstance(act_val, (int, float)):
                    # Within 20% is considered success
                    if exp_val != 0:
                        return abs(act_val - exp_val) / abs(exp_val) < 0.2
                    return act_val == 0

        # Default to success if no clear failure
        return True

    def _calculate_feedback_score(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> float:
        """Calculate feedback score (-1 to 1)"""
        if 'error' in actual:
            return -1.0

        scores = []

        # Compare numeric values
        for key in expected:
            if key in actual:
                exp_val = expected[key]
                act_val = actual[key]

                if isinstance(exp_val, (int, float)) and isinstance(act_val, (int, float)):
                    if exp_val != 0:
                        diff_ratio = (act_val - exp_val) / abs(exp_val)
                        score = max(-1, min(1, 1 - abs(diff_ratio)))
                        scores.append(score)
                elif exp_val == act_val:
                    scores.append(1.0)
                else:
                    scores.append(0.0)

        if scores:
            return np.mean(scores)

        return 0.5 if self._evaluate_success(expected, actual) else -0.5

    # =========================================================================
    # PATTERN DETECTION
    # =========================================================================

    async def _pattern_detection_loop(self):
        """Detect patterns from outcomes"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(600)  # Every 10 minutes

                await self._detect_patterns()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Pattern detection error: {e}")
                await asyncio.sleep(600)

    async def _detect_patterns(self):
        """Detect patterns from recent outcomes"""
        if len(self.recent_outcomes) < 10:
            return

        # Group outcomes by action type
        by_action = defaultdict(list)
        for outcome in self.recent_outcomes:
            by_action[outcome.action_type].append(outcome)

        for action_type, outcomes in by_action.items():
            if len(outcomes) < 5:
                continue

            # Analyze success patterns
            successful = [o for o in outcomes if o.success]
            failed = [o for o in outcomes if not o.success]

            if len(successful) >= 3:
                # Extract common conditions from successful outcomes
                await self._extract_success_pattern(action_type, successful)

            if len(failed) >= 3:
                # Extract common conditions from failed outcomes
                await self._extract_failure_pattern(action_type, failed)

    async def _extract_success_pattern(
        self,
        action_type: str,
        outcomes: List[LearningOutcome]
    ):
        """Extract pattern from successful outcomes"""
        # Find common context elements
        common_context = self._find_common_elements(
            [o.context for o in outcomes]
        )

        if common_context:
            pattern_id = f"success_{action_type}_{uuid.uuid4().hex[:8]}"

            pattern = Pattern(
                id=pattern_id,
                category=PatternCategory.SUCCESSFUL,
                description=f"Successful pattern for {action_type}",
                conditions=common_context,
                outcomes=[{"action": action_type, "success": True}],
                confidence=len(outcomes) / len(self.recent_outcomes),
                occurrence_count=len(outcomes),
                last_seen=datetime.now(),
            )

            self.patterns[pattern_id] = pattern
            self.metrics["patterns_discovered"] += 1

            # Store in database
            await self._store_pattern(pattern)

    async def _extract_failure_pattern(
        self,
        action_type: str,
        outcomes: List[LearningOutcome]
    ):
        """Extract pattern from failed outcomes"""
        common_context = self._find_common_elements(
            [o.context for o in outcomes]
        )

        if common_context:
            pattern_id = f"failure_{action_type}_{uuid.uuid4().hex[:8]}"

            pattern = Pattern(
                id=pattern_id,
                category=PatternCategory.ANOMALOUS,
                description=f"Failure pattern for {action_type}",
                conditions=common_context,
                outcomes=[{"action": action_type, "success": False}],
                confidence=len(outcomes) / len(self.recent_outcomes),
                occurrence_count=len(outcomes),
                last_seen=datetime.now(),
            )

            self.patterns[pattern_id] = pattern
            self.metrics["patterns_discovered"] += 1

            await self._store_pattern(pattern)

    def _find_common_elements(self, contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find common elements across contexts"""
        if not contexts:
            return []

        # Find keys present in all contexts
        common_keys = set(contexts[0].keys())
        for ctx in contexts[1:]:
            common_keys &= set(ctx.keys())

        common_elements = []
        for key in common_keys:
            values = [ctx.get(key) for ctx in contexts]
            # Check if values are similar
            if len(set(str(v) for v in values)) <= len(values) // 2:
                # Most common value
                common_val = max(set(values), key=values.count)
                common_elements.append({"key": key, "value": common_val})

        return common_elements

    async def _store_pattern(self, pattern: Pattern):
        """Store pattern in database"""
        await self._db_execute_with_retry('''
            INSERT INTO brainops_learned_patterns
            (pattern_id, category, description, conditions, outcomes,
             confidence, occurrence_count, last_seen)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (pattern_id) DO UPDATE SET
                confidence = EXCLUDED.confidence,
                occurrence_count = EXCLUDED.occurrence_count,
                last_seen = EXCLUDED.last_seen
        ''',
            pattern.id, pattern.category.value, pattern.description,
            json.dumps(pattern.conditions), json.dumps(pattern.outcomes),
            pattern.confidence, pattern.occurrence_count, pattern.last_seen)

    # =========================================================================
    # KNOWLEDGE SYNTHESIS
    # =========================================================================

    async def _knowledge_synthesis_loop(self):
        """Synthesize knowledge from patterns"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(3600)  # Every hour

                await self._synthesize_knowledge()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Knowledge synthesis error: {e}")
                await asyncio.sleep(3600)

    async def _synthesize_knowledge(self):
        """Synthesize higher-level knowledge from patterns"""
        # Group patterns by category
        by_category = defaultdict(list)
        for pattern in self.patterns.values():
            if pattern.confidence > 0.5:
                by_category[pattern.category].append(pattern)

        # Generate insights
        insights = []

        # Successful patterns -> Best practices
        if by_category[PatternCategory.SUCCESSFUL]:
            for pattern in by_category[PatternCategory.SUCCESSFUL]:
                insights.append({
                    "type": "best_practice",
                    "description": pattern.description,
                    "conditions": pattern.conditions,
                    "confidence": pattern.confidence,
                })

        # Failure patterns -> Warnings
        if by_category[PatternCategory.ANOMALOUS]:
            for pattern in by_category[PatternCategory.ANOMALOUS]:
                insights.append({
                    "type": "warning",
                    "description": f"Avoid: {pattern.description}",
                    "conditions": pattern.conditions,
                    "confidence": pattern.confidence,
                })

        # Store insights if significant
        if insights:
            for insight in insights:
                await self._db_execute_with_retry('''
                    INSERT INTO brainops_learning_suggestions
                    (suggestion_type, description, evidence, priority)
                    VALUES ($1, $2, $3, $4)
                ''',
                    insight['type'],
                    insight['description'],
                    json.dumps(insight.get('conditions', [])),
                    insight.get('confidence', 0.5))

            self.metrics["improvements_suggested"] += len(insights)

    # =========================================================================
    # PERFORMANCE MONITORING
    # =========================================================================

    async def _performance_monitoring_loop(self):
        """Monitor for performance regression"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(1800)  # Every 30 minutes

                await self._check_performance()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(1800)

    async def _check_performance(self):
        """Check for performance regression"""
        # Get recent success rate
        recent = await self._db_fetchrow_with_retry('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes
            FROM brainops_learning_outcomes
            WHERE created_at > NOW() - INTERVAL '1 hour'
        ''')

        if recent and recent['total'] > 10:
            recent_rate = recent['successes'] / recent['total']

            # Get historical success rate
            historical = await self._db_fetchrow_with_retry('''
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes
                FROM brainops_learning_outcomes
                WHERE created_at > NOW() - INTERVAL '24 hours'
                AND created_at < NOW() - INTERVAL '1 hour'
            ''')

            if historical and historical['total'] > 10:
                historical_rate = historical['successes'] / historical['total']

                # Check for regression
                if recent_rate < historical_rate - 0.1:  # 10% drop
                    logger.warning(
                        f"Performance regression detected: "
                        f"{recent_rate:.1%} vs {historical_rate:.1%}"
                    )

                    if self.controller:
                        from .metacognitive_controller import AttentionPriority
                        await self.controller._record_thought({
                            "type": "performance_regression",
                            "recent_rate": recent_rate,
                            "historical_rate": historical_rate,
                        }, AttentionPriority.HIGH, "learning_pipeline")

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def process_learning(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process learning request from controller"""
        learning_type = data.get("type", "outcome")

        if learning_type == "outcome":
            outcome_id = await self.track_outcome(
                decision_id=data.get("decision_id", ""),
                action_type=data.get("action_type", "unknown"),
                expected_result=data.get("expected", {}),
                actual_result=data.get("actual", {}),
                context=data.get("context"),
            )
            return {"status": "tracked", "outcome_id": outcome_id}

        elif learning_type == "feedback":
            # Direct feedback incorporation
            return {"status": "feedback_received"}

        return {"status": "unknown_type"}

    async def detect_patterns(self) -> List[str]:
        """Detect patterns and return insights"""
        insights = []

        for pattern in self.patterns.values():
            if pattern.confidence > 0.7:
                insights.append(pattern.description)

        return insights

    async def trigger_focused_learning(self, focus: str):
        """Trigger focused learning on specific area"""
        logger.info(f"Triggering focused learning on: {focus}")
        # Would implement specific learning logic based on focus area

    async def get_health(self) -> Dict[str, Any]:
        """Get learning pipeline health"""
        active_tasks = sum(1 for t in self._tasks if not t.done())

        return {
            "status": "healthy" if active_tasks == len(self._tasks) else "degraded",
            "score": active_tasks / len(self._tasks) if self._tasks else 1.0,
            "patterns_count": len(self.patterns),
            "outcomes_buffered": len(self.recent_outcomes),
            "metrics": self.metrics.copy(),
        }

    async def shutdown(self):
        """Shutdown the learning pipeline"""
        self._shutdown.set()

        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("LearningPipeline shutdown complete")


# Singleton
_learning_pipeline: Optional[LearningPipeline] = None


def get_learning_pipeline() -> Optional[LearningPipeline]:
    """Get the learning pipeline instance"""
    return _learning_pipeline
