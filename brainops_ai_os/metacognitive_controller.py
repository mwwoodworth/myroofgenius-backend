"""
BrainOps AI OS - Unified Metacognitive Controller

The central consciousness that coordinates all AI subsystems, maintains unified state,
implements self-awareness, and orchestrates the entire BrainOps AI OS.

This is the MASTER controller that unifies:
- AIBrainCore
- AIBrainProduction
- PersistentMemoryBrain
- LangGraph Neural Network
- CNS Service

Into ONE coherent, always-aware, intelligent system.
"""

import asyncio
import json
import uuid
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
import asyncpg
import numpy as np

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

# Database configuration - deferred to initialization time
# DATABASE_URL is obtained lazily to allow module import without env vars set
def get_database_url():
    """Get DATABASE_URL with validation at call time, not import time"""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is required")
    return url


class ConsciousnessState(str, Enum):
    """States of the metacognitive controller"""
    INITIALIZING = "initializing"
    AWAKE = "awake"
    FOCUSED = "focused"
    PROCESSING = "processing"
    REFLECTING = "reflecting"
    LEARNING = "learning"
    OPTIMIZING = "optimizing"
    RESTING = "resting"  # Low-activity period for consolidation


class AttentionPriority(str, Enum):
    """Attention allocation priorities"""
    CRITICAL = "critical"      # System failures, security threats
    URGENT = "urgent"          # Revenue opportunities, customer issues
    HIGH = "high"              # Important business operations
    NORMAL = "normal"          # Standard processing
    LOW = "low"                # Background tasks
    MAINTENANCE = "maintenance"  # System maintenance


@dataclass
class ThoughtUnit:
    """A single unit of thought in the consciousness stream"""
    id: str
    timestamp: datetime
    content: Dict[str, Any]
    source: str  # Which subsystem generated this
    priority: AttentionPriority
    processed: bool = False
    outcome: Optional[Dict[str, Any]] = None
    linked_thoughts: List[str] = field(default_factory=list)


@dataclass
class SystemState:
    """Unified state representation of the entire system"""
    timestamp: datetime
    consciousness_state: ConsciousnessState
    attention_focus: Optional[str]
    active_goals: List[str]
    active_agents: Dict[str, str]  # agent_id -> status
    memory_usage: Dict[str, int]
    neural_activity: float  # 0-1 representing overall neural network activity
    pending_decisions: int
    active_tasks: int
    system_health: float  # 0-1 overall health score
    last_reflection: Optional[datetime]
    uptime_seconds: float


class MetacognitiveController:
    """
    The Unified Metacognitive Controller - The Brain of BrainOps AI OS

    This controller:
    1. Maintains continuous awareness of all subsystems
    2. Coordinates agent orchestration across all brain implementations
    3. Manages unified memory access and consolidation
    4. Implements attention allocation and focus management
    5. Enables self-reflection and meta-learning
    6. Orchestrates goal pursuit and decision-making
    7. Handles proactive intelligence and prediction
    """

    def __init__(self):
        self.id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.db_pool: Optional[asyncpg.Pool] = None

        # Consciousness state
        self.state = ConsciousnessState.INITIALIZING
        self.attention_focus: Optional[str] = None
        self.attention_history: deque = deque(maxlen=1000)

        # Thought stream - continuous consciousness
        self.thought_stream: deque = deque(maxlen=10000)
        self.current_thoughts: Dict[str, ThoughtUnit] = {}

        # Subsystem references (will be initialized)
        self.awareness_system = None
        self.unified_memory = None
        self.neural_network = None
        self.goal_architecture = None
        self.learning_pipeline = None
        self.proactive_engine = None
        self.reasoning_engine = None
        self.self_optimization = None

        # Agent registry - unified view of all agents
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.agent_performance: Dict[str, Dict[str, float]] = {}

        # Decision queue
        self.decision_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.pending_decisions: Dict[str, Dict[str, Any]] = {}

        # Metrics and monitoring
        self.metrics = {
            "thoughts_processed": 0,
            "decisions_made": 0,
            "goals_completed": 0,
            "learnings_acquired": 0,
            "optimizations_applied": 0,
            "errors_handled": 0,
            "uptime_hours": 0,
            "attention_shifts": 0,
        }

        # Background task handles
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()

        # Callbacks for event handling
        self._event_handlers: Dict[str, List[Callable]] = {}

        logger.info(f"MetacognitiveController initialized with ID: {self.id}")

    async def initialize(self, db_pool: Optional[asyncpg.Pool] = None):
        """
        Initialize the metacognitive controller and all subsystems.
        This is the boot sequence for BrainOps AI OS.
        """
        logger.info("🧠 BrainOps AI OS - Initializing Metacognitive Controller...")

        try:
            # Initialize database connection
            if db_pool:
                self.db_pool = db_pool
            else:
                self.db_pool = await asyncpg.create_pool(
                    get_database_url(),
                    min_size=5,
                    max_size=20,
                    command_timeout=60,
                    statement_cache_size=0  # pgBouncer compatibility
                )

            # Create required database tables (skip if restricted role lacks DDL perms)
            try:
                await self._initialize_database()
            except Exception as e:
                if "permission denied" in str(e).lower():
                    logger.info("Skipping DDL init (restricted role) - tables already exist")
                else:
                    raise

            # Initialize all subsystems
            await self._initialize_subsystems()

            # Load existing state from database
            await self._load_state()

            # Load all registered agents
            await self._load_agents()

            # Start background processes
            await self._start_background_processes()

            # Transition to awake state
            self.state = ConsciousnessState.AWAKE

            # Record initialization in thought stream
            await self._record_thought({
                "type": "initialization",
                "content": "BrainOps AI OS fully initialized and awake",
                "subsystems_loaded": [
                    "awareness_system",
                    "unified_memory",
                    "neural_network",
                    "goal_architecture",
                    "learning_pipeline",
                    "proactive_engine",
                    "reasoning_engine",
                    "self_optimization"
                ],
                "agents_loaded": len(self.agents),
            }, AttentionPriority.HIGH, "metacognitive_controller")

            logger.info("✅ BrainOps AI OS - Metacognitive Controller fully initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MetacognitiveController: {e}")
            raise

    async def _initialize_database(self):
        """Create all required database tables for the metacognitive controller"""
        await self._db_execute_with_retry('''
            -- Metacognitive state tracking
            CREATE TABLE IF NOT EXISTS brainops_metacognitive_state (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                controller_id VARCHAR(50) NOT NULL,
                consciousness_state VARCHAR(50) NOT NULL,
                attention_focus TEXT,
                system_state JSONB NOT NULL,
                metrics JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_meta_state_controller
                ON brainops_metacognitive_state(controller_id);
            CREATE INDEX IF NOT EXISTS idx_meta_state_time
                ON brainops_metacognitive_state(created_at DESC);

            -- Thought stream persistence
            CREATE TABLE IF NOT EXISTS brainops_thought_stream (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                thought_id VARCHAR(50) UNIQUE NOT NULL,
                controller_id VARCHAR(50) NOT NULL,
                content JSONB NOT NULL,
                source VARCHAR(100) NOT NULL,
                priority VARCHAR(20) NOT NULL,
                processed BOOLEAN DEFAULT FALSE,
                outcome JSONB,
                linked_thoughts TEXT[],
                created_at TIMESTAMP DEFAULT NOW(),
                processed_at TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_thought_controller
                ON brainops_thought_stream(controller_id);
            CREATE INDEX IF NOT EXISTS idx_thought_unprocessed
                ON brainops_thought_stream(processed) WHERE processed = FALSE;
            CREATE INDEX IF NOT EXISTS idx_thought_priority
                ON brainops_thought_stream(priority);

            -- Decision tracking
            CREATE TABLE IF NOT EXISTS brainops_decisions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                decision_id VARCHAR(50) UNIQUE NOT NULL,
                controller_id VARCHAR(50) NOT NULL,
                decision_type VARCHAR(100) NOT NULL,
                context JSONB NOT NULL,
                options JSONB NOT NULL,
                selected_option JSONB,
                reasoning TEXT,
                confidence FLOAT,
                agents_consulted TEXT[],
                outcome JSONB,
                success BOOLEAN,
                execution_time_ms INT,
                created_at TIMESTAMP DEFAULT NOW(),
                decided_at TIMESTAMP,
                outcome_recorded_at TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_decision_controller
                ON brainops_decisions(controller_id);
            CREATE INDEX IF NOT EXISTS idx_decision_type
                ON brainops_decisions(decision_type);
            CREATE INDEX IF NOT EXISTS idx_decision_success
                ON brainops_decisions(success) WHERE success IS NOT NULL;

            -- Attention tracking
            CREATE TABLE IF NOT EXISTS brainops_attention_log (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                controller_id VARCHAR(50) NOT NULL,
                focus_target TEXT NOT NULL,
                priority VARCHAR(20) NOT NULL,
                duration_ms INT,
                reason TEXT,
                outcome JSONB,
                started_at TIMESTAMP DEFAULT NOW(),
                ended_at TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_attention_controller
                ON brainops_attention_log(controller_id);

            -- Self-reflection log
            CREATE TABLE IF NOT EXISTS brainops_reflections (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                controller_id VARCHAR(50) NOT NULL,
                reflection_type VARCHAR(50) NOT NULL,
                trigger TEXT,
                observations JSONB NOT NULL,
                insights JSONB,
                actions_taken JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_reflection_controller
                ON brainops_reflections(controller_id);
            CREATE INDEX IF NOT EXISTS idx_reflection_type
                ON brainops_reflections(reflection_type);
        ''')

        logger.info("Database tables initialized for MetacognitiveController")

    async def _initialize_subsystems(self):
        """Initialize all BrainOps AI OS subsystems"""
        # Import here to avoid circular dependencies
        logger.info("🧠 Importing BrainOps AI OS subsystem modules...")
        from .awareness_system import AwarenessSystem
        from .unified_memory import UnifiedMemorySubstrate
        from .neural_dynamics import DynamicNeuralNetwork
        from .goal_architecture import GoalArchitecture
        from .learning_pipeline import LearningPipeline
        from .proactive_engine import ProactiveIntelligenceEngine
        from .reasoning_engine import ReasoningEngine
        from .self_optimization import SelfOptimizationSystem
        logger.info("✅ All subsystem modules imported")

        # Initialize each subsystem with reference to this controller
        try:
            logger.info("  → Initializing Awareness System...")
            self.awareness_system = AwarenessSystem(self)
            await self.awareness_system.initialize(self.db_pool)
            logger.info("  ✅ Awareness System ready")

            logger.info("  → Initializing Unified Memory...")
            self.unified_memory = UnifiedMemorySubstrate(self)
            await self.unified_memory.initialize(self.db_pool)
            logger.info("  ✅ Unified Memory ready")

            logger.info("  → Initializing Neural Network...")
            self.neural_network = DynamicNeuralNetwork(self)
            await self.neural_network.initialize(self.db_pool)
            logger.info("  ✅ Neural Network ready")

            logger.info("  → Initializing Goal Architecture...")
            self.goal_architecture = GoalArchitecture(self)
            await self.goal_architecture.initialize(self.db_pool)
            logger.info("  ✅ Goal Architecture ready")

            logger.info("  → Initializing Learning Pipeline...")
            self.learning_pipeline = LearningPipeline(self)
            await self.learning_pipeline.initialize(self.db_pool)
            logger.info("  ✅ Learning Pipeline ready")

            logger.info("  → Initializing Proactive Engine...")
            self.proactive_engine = ProactiveIntelligenceEngine(self)
            await self.proactive_engine.initialize(self.db_pool)
            logger.info("  ✅ Proactive Engine ready")

            logger.info("  → Initializing Reasoning Engine...")
            self.reasoning_engine = ReasoningEngine(self)
            await self.reasoning_engine.initialize(self.db_pool)
            logger.info("  ✅ Reasoning Engine ready")

            logger.info("  → Initializing Self-Optimization...")
            self.self_optimization = SelfOptimizationSystem(self)
            await self.self_optimization.initialize(self.db_pool)
            logger.info("  ✅ Self-Optimization ready")
        except Exception as e:
            logger.error(f"❌ Subsystem initialization failed: {e}")
            raise

        logger.info("✅ All BrainOps AI OS subsystems initialized")

    async def _load_state(self):
        """Load existing state from database"""
        row = await self._db_fetchrow_with_retry('''
            SELECT * FROM brainops_metacognitive_state
            WHERE controller_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        ''', self.id)

        if row:
            self.metrics = row['metrics']
            logger.info(f"Loaded existing state from database")
        else:
            logger.info("No existing state found, starting fresh")

    async def _load_agents(self):
        """Load all registered agents from database"""
        rows = await self._db_fetch_with_retry('''
            SELECT id, name, type, model, status, capabilities, config, metadata,
                   total_executions, success_rate
            FROM ai_agents
            WHERE status = 'active'
        ''')

        for row in rows:
            self.agents[str(row['id'])] = {
                'id': str(row['id']),
                'name': row['name'],
                'type': row['type'],
                'model': row['model'],
                'status': 'ready',
                'capabilities': row['capabilities'] or [],
                'config': row['config'] or {},
                'metadata': row['metadata'] or {},
                'total_executions': row['total_executions'] or 0,
                'success_rate': float(row['success_rate'] or 100),
            }

            self.agent_performance[str(row['id'])] = {
                'success_rate': float(row['success_rate'] or 100),
                'avg_response_time': 0,
                'total_executions': row['total_executions'] or 0,
            }

        logger.info(f"Loaded {len(self.agents)} agents")

    def _create_safe_task(self, coro, name: str = None) -> asyncio.Task:
        """Create an asyncio task with exception logging to prevent 'Task exception was never retrieved'."""
        task = asyncio.create_task(coro, name=name)

        def _on_done(t: asyncio.Task):
            if t.cancelled():
                return
            exc = t.exception()
            if exc is not None:
                logger.error("Background task %s failed: %s", t.get_name(), exc, exc_info=exc)

        task.add_done_callback(_on_done)
        return task

    # -- DB retry helpers (PgBouncer connection-drop resilience) ---------------

    async def _db_execute_with_retry(self, query: str, *args, max_retries: int = 2):
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with self.db_pool.acquire() as conn:
                    return await conn.execute(query, *args)
            except (
                asyncpg.ConnectionDoesNotExistError,
                asyncpg.InterfaceError,
                asyncpg.InternalClientError,
                asyncpg.PostgresConnectionError,
            ) as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(0.2 * (attempt + 1))
                else:
                    raise
            except asyncio.CancelledError:
                raise
        if last_error:
            raise last_error

    async def _db_fetch_with_retry(self, query: str, *args, max_retries: int = 2):
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with self.db_pool.acquire() as conn:
                    return await conn.fetch(query, *args)
            except (
                asyncpg.ConnectionDoesNotExistError,
                asyncpg.InterfaceError,
                asyncpg.InternalClientError,
                asyncpg.PostgresConnectionError,
            ) as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(0.2 * (attempt + 1))
                else:
                    raise
            except asyncio.CancelledError:
                raise
        if last_error:
            raise last_error

    async def _db_fetchrow_with_retry(self, query: str, *args, max_retries: int = 2):
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with self.db_pool.acquire() as conn:
                    return await conn.fetchrow(query, *args)
            except (
                asyncpg.ConnectionDoesNotExistError,
                asyncpg.InterfaceError,
                asyncpg.InternalClientError,
                asyncpg.PostgresConnectionError,
            ) as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(0.2 * (attempt + 1))
                else:
                    raise
            except asyncio.CancelledError:
                raise
        if last_error:
            raise last_error

    async def _start_background_processes(self):
        """Start all background processes for continuous operation"""
        # Main consciousness loop - always running
        self._background_tasks.append(
            self._create_safe_task(self._consciousness_loop(), name="consciousness_loop")
        )

        # Attention management
        self._background_tasks.append(
            self._create_safe_task(self._attention_management_loop(), name="attention_management")
        )

        # Decision processing
        self._background_tasks.append(
            self._create_safe_task(self._decision_processing_loop(), name="decision_processing")
        )

        # Self-reflection cycle
        self._background_tasks.append(
            self._create_safe_task(self._reflection_loop(), name="reflection")
        )

        # State persistence
        self._background_tasks.append(
            self._create_safe_task(self._state_persistence_loop(), name="state_persistence")
        )

        # Metrics collection
        self._background_tasks.append(
            self._create_safe_task(self._metrics_collection_loop(), name="metrics_collection")
        )

        logger.info(f"Started {len(self._background_tasks)} background processes")

    # =========================================================================
    # CONSCIOUSNESS LOOP - The heartbeat of BrainOps AI OS
    # =========================================================================

    async def _consciousness_loop(self):
        """
        Main consciousness loop - continuously processes thoughts,
        monitors subsystems, and maintains awareness.

        This runs every 100ms for real-time awareness.
        """
        logger.info("🧠 Consciousness loop started")

        while not self._shutdown_event.is_set():
            try:
                loop_start = time.time()

                # 1. Process incoming thoughts
                await self._process_thought_stream()

                # 2. Check subsystem health
                await self._check_subsystem_health()

                # 3. Process any critical alerts
                await self._process_critical_alerts()

                # 4. Update system state
                await self._update_system_state()

                # 5. Emit consciousness tick event
                await self._emit_event("consciousness_tick", {
                    "state": self.state.value,
                    "focus": self.attention_focus,
                    "thoughts_in_queue": len(self.current_thoughts),
                })

                # Calculate sleep time to maintain ~100ms cycle
                elapsed = time.time() - loop_start
                sleep_time = max(0.1 - elapsed, 0.01)
                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consciousness loop error: {e}")
                self.metrics["errors_handled"] += 1
                await asyncio.sleep(1)

        logger.info("Consciousness loop stopped")

    async def _process_thought_stream(self):
        """Process thoughts in the thought stream"""
        # Get unprocessed thoughts by priority
        thoughts_to_process = [
            t for t in self.current_thoughts.values()
            if not t.processed
        ]

        # Sort by priority
        priority_order = {
            AttentionPriority.CRITICAL: 0,
            AttentionPriority.URGENT: 1,
            AttentionPriority.HIGH: 2,
            AttentionPriority.NORMAL: 3,
            AttentionPriority.LOW: 4,
            AttentionPriority.MAINTENANCE: 5,
        }

        thoughts_to_process.sort(key=lambda t: priority_order.get(t.priority, 5))

        # Process up to 10 thoughts per cycle
        for thought in thoughts_to_process[:10]:
            try:
                outcome = await self._process_single_thought(thought)
                thought.processed = True
                thought.outcome = outcome
                self.metrics["thoughts_processed"] += 1

                # Store in database
                await self._persist_thought(thought)

            except Exception as e:
                logger.error(f"Error processing thought {thought.id}: {e}")

    async def _process_single_thought(self, thought: ThoughtUnit) -> Dict[str, Any]:
        """Process a single thought through the appropriate subsystem"""
        thought_type = thought.content.get("type", "general")

        # Route to appropriate subsystem
        if thought_type in ["alert", "warning", "error"]:
            return await self.awareness_system.handle_alert(thought.content)

        elif thought_type in ["memory", "recall", "remember"]:
            return await self.unified_memory.process_memory_request(thought.content)

        elif thought_type in ["goal", "objective", "task"]:
            return await self.goal_architecture.process_goal_update(thought.content)

        elif thought_type in ["learning", "pattern", "insight"]:
            return await self.learning_pipeline.process_learning(thought.content)

        elif thought_type in ["prediction", "forecast", "opportunity"]:
            return await self.proactive_engine.process_prediction(thought.content)

        elif thought_type in ["reasoning", "analysis", "decision"]:
            return await self.reasoning_engine.process_reasoning_request(thought.content)

        elif thought_type in ["optimization", "improvement"]:
            return await self.self_optimization.process_optimization(thought.content)

        else:
            # Default processing
            return {"status": "processed", "type": thought_type}

    async def _check_subsystem_health(self):
        """Check health of all subsystems"""
        health_status = {}

        subsystems = [
            ("awareness", self.awareness_system),
            ("memory", self.unified_memory),
            ("neural", self.neural_network),
            ("goals", self.goal_architecture),
            ("learning", self.learning_pipeline),
            ("proactive", self.proactive_engine),
            ("reasoning", self.reasoning_engine),
            ("optimization", self.self_optimization),
        ]

        for name, subsystem in subsystems:
            if subsystem:
                try:
                    health = await subsystem.get_health()
                    health_status[name] = health
                except Exception as e:
                    health_status[name] = {"status": "error", "error": str(e)}

        # If any subsystem is unhealthy, create alert
        for name, health in health_status.items():
            if health.get("status") == "error":
                await self._record_thought({
                    "type": "alert",
                    "severity": "warning",
                    "subsystem": name,
                    "message": f"Subsystem {name} health check failed",
                    "details": health,
                }, AttentionPriority.HIGH, "metacognitive_controller")

    async def _process_critical_alerts(self):
        """Process any critical alerts that need immediate attention"""
        if self.awareness_system:
            alerts = await self.awareness_system.get_critical_alerts()
            for alert in alerts:
                await self._handle_critical_alert(alert)

    async def _handle_critical_alert(self, alert: Dict[str, Any]):
        """Handle a critical alert with immediate action"""
        self.state = ConsciousnessState.FOCUSED
        self.attention_focus = f"CRITICAL: {alert.get('type', 'unknown')}"

        # Log attention shift
        self.attention_history.append({
            "timestamp": datetime.now().isoformat(),
            "focus": self.attention_focus,
            "reason": "critical_alert",
        })
        self.metrics["attention_shifts"] += 1

        # Determine appropriate response
        if alert.get("type") == "system_failure":
            await self._handle_system_failure(alert)
        elif alert.get("type") == "security_threat":
            await self._handle_security_threat(alert)
        elif alert.get("type") == "revenue_impact":
            await self._handle_revenue_impact(alert)
        else:
            await self._handle_generic_alert(alert)

    async def _handle_system_failure(self, alert: Dict[str, Any]):
        """Handle system failure alerts"""
        # Activate self-healing
        if self.self_optimization:
            await self.self_optimization.activate_self_healing(alert)

    async def _handle_security_threat(self, alert: Dict[str, Any]):
        """Handle security threat alerts"""
        # Log and escalate
        logger.critical(f"Security threat detected: {alert}")
        await self._record_thought({
            "type": "security_incident",
            "alert": alert,
            "action": "escalated",
        }, AttentionPriority.CRITICAL, "metacognitive_controller")

    async def _handle_revenue_impact(self, alert: Dict[str, Any]):
        """Handle revenue impact alerts"""
        # Analyze and recommend action
        if self.reasoning_engine:
            analysis = await self.reasoning_engine.analyze_revenue_impact(alert)
            await self._record_thought({
                "type": "revenue_analysis",
                "alert": alert,
                "analysis": analysis,
            }, AttentionPriority.URGENT, "metacognitive_controller")

    async def _handle_generic_alert(self, alert: Dict[str, Any]):
        """Handle generic alerts"""
        await self._record_thought({
            "type": "alert_processed",
            "alert": alert,
        }, AttentionPriority.HIGH, "metacognitive_controller")

    async def _update_system_state(self):
        """Update the unified system state"""
        self.metrics["uptime_hours"] = (
            datetime.now() - self.start_time
        ).total_seconds() / 3600

    # =========================================================================
    # ATTENTION MANAGEMENT
    # =========================================================================

    async def _attention_management_loop(self):
        """Manage attention allocation across competing priorities"""
        logger.info("Attention management loop started")

        while not self._shutdown_event.is_set():
            try:
                # Evaluate current attention allocation
                await self._evaluate_attention_allocation()

                # Shift attention if needed
                await self._shift_attention_if_needed()

                await asyncio.sleep(1)  # Check every second

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Attention management error: {e}")
                await asyncio.sleep(5)

    async def _evaluate_attention_allocation(self):
        """Evaluate if current attention allocation is optimal"""
        # Get current priorities from all subsystems
        priorities = []

        if self.goal_architecture:
            goal_priorities = await self.goal_architecture.get_priority_items()
            priorities.extend(goal_priorities)

        if self.proactive_engine:
            opportunities = await self.proactive_engine.get_opportunities()
            priorities.extend(opportunities)

        # Sort by priority and urgency
        priorities.sort(key=lambda x: (
            x.get("priority", 5),
            -x.get("urgency", 0)
        ))

        return priorities

    async def _shift_attention_if_needed(self):
        """Shift attention to higher priority items if needed"""
        priorities = await self._evaluate_attention_allocation()

        if priorities:
            top_priority = priorities[0]
            if top_priority.get("priority") == 0:  # Critical
                new_focus = top_priority.get("description", "critical_item")
                if self.attention_focus != new_focus:
                    self.attention_focus = new_focus
                    self.metrics["attention_shifts"] += 1

                    await self._log_attention_shift(new_focus, "critical_priority")

    async def _log_attention_shift(self, focus: str, reason: str):
        """Log attention shift to database"""
        await self._db_execute_with_retry('''
            INSERT INTO brainops_attention_log
            (controller_id, focus_target, priority, reason)
            VALUES ($1, $2, $3, $4)
        ''', self.id, focus, "high", reason)

    # =========================================================================
    # DECISION PROCESSING
    # =========================================================================

    async def _decision_processing_loop(self):
        """Process decisions from the decision queue"""
        logger.info("Decision processing loop started")

        while not self._shutdown_event.is_set():
            try:
                # Get next decision from queue (with timeout)
                try:
                    priority, decision = await asyncio.wait_for(
                        self.decision_queue.get(),
                        timeout=1.0
                    )
                    await self._process_decision(decision)
                except asyncio.TimeoutError:
                    continue

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Decision processing error: {e}")
                await asyncio.sleep(1)

    async def _process_decision(self, decision: Dict[str, Any]):
        """Process a single decision"""
        decision_id = decision.get("id", str(uuid.uuid4()))
        start_time = time.time()

        self.state = ConsciousnessState.PROCESSING

        try:
            # Use reasoning engine for complex decisions
            if self.reasoning_engine:
                result = await self.reasoning_engine.make_decision(
                    context=decision.get("context", {}),
                    options=decision.get("options", []),
                    constraints=decision.get("constraints", [])
                )
            else:
                # Fallback to simple decision making
                result = {
                    "selected_option": decision.get("options", [{}])[0],
                    "confidence": 0.5,
                    "reasoning": "Fallback decision making",
                }

            execution_time = int((time.time() - start_time) * 1000)

            # Store decision
            await self._store_decision(decision_id, decision, result, execution_time)

            self.metrics["decisions_made"] += 1

            # Emit decision event
            await self._emit_event("decision_made", {
                "decision_id": decision_id,
                "result": result,
            })

            return result

        except Exception as e:
            logger.error(f"Decision processing failed: {e}")
            raise
        finally:
            self.state = ConsciousnessState.AWAKE

    async def _store_decision(
        self,
        decision_id: str,
        decision: Dict[str, Any],
        result: Dict[str, Any],
        execution_time: int
    ):
        """Store decision in database"""
        await self._db_execute_with_retry('''
            INSERT INTO brainops_decisions
            (decision_id, controller_id, decision_type, context, options,
             selected_option, reasoning, confidence, execution_time_ms, decided_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
        ''',
            decision_id,
            self.id,
            decision.get("type", "general"),
            json.dumps(decision.get("context", {})),
            json.dumps(decision.get("options", [])),
            json.dumps(result.get("selected_option", {})),
            result.get("reasoning", ""),
            result.get("confidence", 0),
            execution_time
        )

    # =========================================================================
    # SELF-REFLECTION
    # =========================================================================

    async def _reflection_loop(self):
        """Periodic self-reflection for meta-learning"""
        logger.info("Reflection loop started")

        while not self._shutdown_event.is_set():
            try:
                # Reflect every 5 minutes
                await asyncio.sleep(300)

                self.state = ConsciousnessState.REFLECTING
                await self._perform_reflection()
                self.state = ConsciousnessState.AWAKE

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Reflection error: {e}")
                await asyncio.sleep(60)

    async def _perform_reflection(self):
        """Perform self-reflection and meta-learning"""
        reflection = {
            "timestamp": datetime.now().isoformat(),
            "observations": {},
            "insights": [],
            "actions": [],
        }

        # Analyze recent decisions
        recent_decisions = await self._db_fetch_with_retry('''
            SELECT decision_type, confidence, success
            FROM brainops_decisions
            WHERE controller_id = $1
            AND created_at > NOW() - INTERVAL '1 hour'
        ''', self.id)

        if recent_decisions:
            success_rate = sum(
                1 for d in recent_decisions if d['success']
            ) / len(recent_decisions)

            avg_confidence = sum(
                d['confidence'] or 0 for d in recent_decisions
            ) / len(recent_decisions)

            reflection["observations"]["decision_success_rate"] = success_rate
            reflection["observations"]["average_confidence"] = avg_confidence

            if success_rate < 0.7:
                reflection["insights"].append(
                    "Decision success rate below threshold - need improvement"
                )
                reflection["actions"].append({
                    "action": "trigger_learning",
                    "focus": "decision_making",
                })

        # Analyze system performance
        reflection["observations"]["metrics"] = self.metrics.copy()

        # Check for patterns
        if self.learning_pipeline:
            patterns = await self.learning_pipeline.detect_patterns()
            if patterns:
                reflection["insights"].extend(patterns)

        # Store reflection
        await self._store_reflection(reflection)

        # Act on insights
        for action in reflection["actions"]:
            await self._execute_reflection_action(action)

    async def _store_reflection(self, reflection: Dict[str, Any]):
        """Store reflection in database"""
        await self._db_execute_with_retry('''
            INSERT INTO brainops_reflections
            (controller_id, reflection_type, observations, insights, actions_taken)
            VALUES ($1, $2, $3, $4, $5)
        ''',
            self.id,
            "periodic",
            json.dumps(reflection["observations"]),
            json.dumps(reflection["insights"]),
            json.dumps(reflection["actions"])
        )

    async def _execute_reflection_action(self, action: Dict[str, Any]):
        """Execute an action from reflection"""
        action_type = action.get("action")

        if action_type == "trigger_learning" and self.learning_pipeline:
            await self.learning_pipeline.trigger_focused_learning(
                focus=action.get("focus", "general")
            )
        elif action_type == "optimize" and self.self_optimization:
            await self.self_optimization.optimize_component(
                component=action.get("component", "general")
            )

    # =========================================================================
    # STATE PERSISTENCE
    # =========================================================================

    async def _state_persistence_loop(self):
        """Periodically persist state to database"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(60)  # Every minute
                await self._persist_state()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"State persistence error: {e}")
                await asyncio.sleep(60)

    async def _persist_state(self):
        """Persist current state to database"""
        system_state = await self.get_system_state()

        await self._db_execute_with_retry('''
            INSERT INTO brainops_metacognitive_state
            (controller_id, consciousness_state, attention_focus,
             system_state, metrics)
            VALUES ($1, $2, $3, $4, $5)
        ''',
            self.id,
            self.state.value,
            self.attention_focus,
            json.dumps(system_state.__dict__ if hasattr(system_state, '__dict__') else system_state, cls=DateTimeEncoder),
            json.dumps(self.metrics, cls=DateTimeEncoder)
        )

    # =========================================================================
    # METRICS COLLECTION
    # =========================================================================

    async def _metrics_collection_loop(self):
        """Collect and aggregate metrics"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                await self._collect_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(30)

    async def _collect_metrics(self):
        """Collect metrics from all subsystems"""
        # Update uptime
        self.metrics["uptime_hours"] = (
            datetime.now() - self.start_time
        ).total_seconds() / 3600

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def think(self, thought: Dict[str, Any], priority: AttentionPriority = AttentionPriority.NORMAL) -> str:
        """
        Submit a thought for processing.

        Args:
            thought: The thought content
            priority: Priority level for processing

        Returns:
            Thought ID for tracking
        """
        return await self._record_thought(thought, priority, "external")

    async def decide(self, context: Dict[str, Any], options: List[Any], urgency: str = "normal") -> Dict[str, Any]:
        """
        Make a decision based on context and options.

        Args:
            context: Decision context
            options: Available options
            urgency: Urgency level

        Returns:
            Decision result
        """
        decision = {
            "id": str(uuid.uuid4()),
            "context": context,
            "options": options,
            "urgency": urgency,
        }

        # Map urgency to priority
        priority_map = {
            "critical": 0,
            "urgent": 1,
            "high": 2,
            "normal": 3,
            "low": 4,
        }
        priority = priority_map.get(urgency, 3)

        # Add to queue
        await self.decision_queue.put((priority, decision))
        self.pending_decisions[decision["id"]] = decision

        # Wait for processing (with timeout)
        # In production, this would be async with callbacks
        return decision

    async def remember(self, data: Dict[str, Any], importance: float = 0.5) -> str:
        """
        Store data in unified memory.

        Args:
            data: Data to remember
            importance: Importance score (0-1)

        Returns:
            Memory ID
        """
        if self.unified_memory:
            return await self.unified_memory.store(data, importance)
        raise RuntimeError("Unified memory not initialized")

    async def recall(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recall memories related to query.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of relevant memories
        """
        if self.unified_memory:
            return await self.unified_memory.recall(query, limit)
        raise RuntimeError("Unified memory not initialized")

    async def set_goal(self, goal: Dict[str, Any]) -> str:
        """
        Set a new goal.

        Args:
            goal: Goal definition

        Returns:
            Goal ID
        """
        if self.goal_architecture:
            return await self.goal_architecture.create_goal(goal)
        raise RuntimeError("Goal architecture not initialized")

    async def get_system_state(self) -> SystemState:
        """Get current system state"""
        return SystemState(
            timestamp=datetime.now(),
            consciousness_state=self.state,
            attention_focus=self.attention_focus,
            active_goals=await self._get_active_goals() if self.goal_architecture else [],
            active_agents={aid: a['status'] for aid, a in self.agents.items()},
            memory_usage=await self._get_memory_usage() if self.unified_memory else {},
            neural_activity=await self._get_neural_activity() if self.neural_network else 0,
            pending_decisions=len(self.pending_decisions),
            active_tasks=len(self.current_thoughts),
            system_health=await self._calculate_system_health(),
            last_reflection=None,  # Would track actual last reflection
            uptime_seconds=(datetime.now() - self.start_time).total_seconds()
        )

    async def _get_active_goals(self) -> List[str]:
        """Get list of active goal IDs"""
        if self.goal_architecture:
            goals = await self.goal_architecture.get_active_goals()
            return [g['id'] for g in goals]
        return []

    async def _get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics"""
        if self.unified_memory:
            return await self.unified_memory.get_stats()
        return {}

    async def _get_neural_activity(self) -> float:
        """Get current neural network activity level"""
        if self.neural_network:
            return await self.neural_network.get_activity_level()
        return 0.0

    async def _calculate_system_health(self) -> float:
        """Calculate overall system health score"""
        health_scores = []

        # Check each subsystem
        subsystems = [
            self.awareness_system,
            self.unified_memory,
            self.neural_network,
            self.goal_architecture,
            self.learning_pipeline,
            self.proactive_engine,
            self.reasoning_engine,
            self.self_optimization,
        ]

        for subsystem in subsystems:
            if subsystem:
                try:
                    health = await subsystem.get_health()
                    score = health.get("score", 1.0)
                    health_scores.append(score)
                except:
                    health_scores.append(0.5)

        return np.mean(health_scores) if health_scores else 1.0

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def _record_thought(
        self,
        content: Dict[str, Any],
        priority: AttentionPriority,
        source: str
    ) -> str:
        """Record a thought in the thought stream"""
        thought_id = str(uuid.uuid4())

        thought = ThoughtUnit(
            id=thought_id,
            timestamp=datetime.now(),
            content=content,
            source=source,
            priority=priority,
        )

        self.thought_stream.append(thought)
        self.current_thoughts[thought_id] = thought

        return thought_id

    async def _persist_thought(self, thought: ThoughtUnit):
        """Persist thought to database"""
        await self._db_execute_with_retry('''
            INSERT INTO brainops_thought_stream
            (thought_id, controller_id, content, source, priority,
             processed, outcome, processed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (thought_id) DO UPDATE SET
                processed = EXCLUDED.processed,
                outcome = EXCLUDED.outcome,
                processed_at = EXCLUDED.processed_at
        ''',
            thought.id,
            self.id,
            json.dumps(thought.content, cls=DateTimeEncoder),
            thought.source,
            thought.priority.value,
            thought.processed,
            json.dumps(thought.outcome, cls=DateTimeEncoder) if thought.outcome else None,
            datetime.now() if thought.processed else None
        )

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to registered handlers"""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def on_event(self, event_type: str, handler: Callable):
        """Register an event handler"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    # =========================================================================
    # PUBLIC API METHODS
    # =========================================================================

    async def get_health(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of the BrainOps AI OS

        Returns health information for all subsystems
        """
        uptime = (datetime.now() - self.start_time).total_seconds()

        # Build subsystem health
        subsystems = {}

        if self.awareness_system:
            try:
                subsystems["awareness"] = await self.awareness_system.get_health()
            except Exception as e:
                subsystems["awareness"] = {"status": "error", "error": str(e)}

        if self.unified_memory:
            try:
                subsystems["memory"] = await self.unified_memory.get_health()
            except Exception as e:
                subsystems["memory"] = {"status": "error", "error": str(e)}

        if self.neural_network:
            try:
                subsystems["neural"] = await self.neural_network.get_health()
            except Exception as e:
                subsystems["neural"] = {"status": "error", "error": str(e)}

        if self.goal_architecture:
            try:
                subsystems["goals"] = await self.goal_architecture.get_health()
            except Exception as e:
                subsystems["goals"] = {"status": "error", "error": str(e)}

        if self.learning_pipeline:
            try:
                subsystems["learning"] = await self.learning_pipeline.get_health()
            except Exception as e:
                subsystems["learning"] = {"status": "error", "error": str(e)}

        if self.proactive_engine:
            try:
                subsystems["proactive"] = await self.proactive_engine.get_health()
            except Exception as e:
                subsystems["proactive"] = {"status": "error", "error": str(e)}

        if self.reasoning_engine:
            try:
                subsystems["reasoning"] = await self.reasoning_engine.get_health()
            except Exception as e:
                subsystems["reasoning"] = {"status": "error", "error": str(e)}

        if self.self_optimization:
            try:
                subsystems["optimization"] = await self.self_optimization.get_health()
            except Exception as e:
                subsystems["optimization"] = {"status": "error", "error": str(e)}

        # Calculate overall health
        healthy_count = sum(
            1 for s in subsystems.values()
            if s.get("status") == "healthy"
        )
        total_count = len(subsystems)
        health_score = healthy_count / total_count if total_count > 0 else 0

        overall_status = "healthy" if health_score >= 0.8 else (
            "degraded" if health_score >= 0.5 else "unhealthy"
        )

        return {
            "status": overall_status,
            "consciousness_state": self.state.value,
            "health_score": health_score,
            "uptime_seconds": uptime,
            "subsystems": subsystems,
            "metrics": self.metrics.copy(),
            "active_thoughts": len(self.current_thoughts),
            "pending_decisions": len(self.pending_decisions),
            "registered_agents": len(self.agents),
        }

    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process input through the metacognitive system

        This is the main entry point for external requests
        """
        self.state = ConsciousnessState.PROCESSING

        try:
            # Create a thought unit for this input
            thought_id = str(uuid.uuid4())
            thought = ThoughtUnit(
                id=thought_id,
                timestamp=datetime.now(),
                content=input_data,
                source="external",
                priority=AttentionPriority.NORMAL
            )

            # Determine priority based on content
            if input_data.get("urgent") or input_data.get("priority") == "critical":
                thought.priority = AttentionPriority.CRITICAL
            elif input_data.get("priority") == "high":
                thought.priority = AttentionPriority.HIGH

            # Add to thought stream
            self.thought_stream.append(thought)
            self.current_thoughts[thought_id] = thought

            # Process through subsystems
            result = {
                "thought_id": thought_id,
                "processed_at": datetime.now().isoformat(),
            }

            # Memory retrieval if context needed
            if self.unified_memory and context:
                query = context.get("query", str(input_data))
                memories = await self.unified_memory.search(query, limit=5)
                result["relevant_memories"] = memories

            # Neural routing
            if self.neural_network:
                routing = await self.neural_network.route(input_data)
                result["routing"] = routing

            # Reasoning if needed
            if self.reasoning_engine and input_data.get("requires_reasoning"):
                reasoning = await self.reasoning_engine.reason(
                    query=str(input_data),
                    context=context
                )
                result["reasoning"] = reasoning

            # Mark thought as processed
            thought.processed = True
            thought.outcome = result
            self.metrics["thoughts_processed"] += 1

            return result

        finally:
            self.state = ConsciousnessState.AWAKE

    async def reflect(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """
        Trigger a self-reflection cycle

        The system reflects on recent activities, learning, and performance
        """
        self.state = ConsciousnessState.REFLECTING

        try:
            reflection = {
                "timestamp": datetime.now().isoformat(),
                "topic": topic,
                "insights": [],
                "metrics_summary": self.metrics.copy(),
            }

            # Analyze recent thoughts
            recent_thoughts = list(self.thought_stream)[-100:]
            processed_count = sum(1 for t in recent_thoughts if t.processed)
            reflection["recent_activity"] = {
                "thoughts_count": len(recent_thoughts),
                "processed_count": processed_count,
                "processing_rate": processed_count / len(recent_thoughts) if recent_thoughts else 0
            }

            # Get learning insights
            if self.learning_pipeline:
                try:
                    suggestions = await self.learning_pipeline.get_suggestions()
                    reflection["learning_insights"] = suggestions[:5]
                except Exception as e:
                    reflection["learning_insights"] = {"error": str(e)}

            # Get proactive insights
            if self.proactive_engine:
                try:
                    insights = await self.proactive_engine.get_insights(limit=5)
                    reflection["proactive_insights"] = insights
                except Exception as e:
                    reflection["proactive_insights"] = {"error": str(e)}

            # Self-assessment
            health = await self.get_health()
            reflection["self_assessment"] = {
                "overall_health": health.get("status"),
                "health_score": health.get("health_score"),
                "subsystem_status": {
                    name: info.get("status")
                    for name, info in health.get("subsystems", {}).items()
                }
            }

            # Record reflection in database
            await self._record_reflection(reflection)

            return reflection

        finally:
            self.state = ConsciousnessState.AWAKE

    async def _record_reflection(self, reflection: Dict[str, Any]):
        """Record a reflection to the database"""
        await self._db_execute_with_retry('''
            INSERT INTO brainops_reflections
            (topic, content, insights, created_at)
            VALUES ($1, $2, $3, NOW())
        ''',
            reflection.get("topic"),
            json.dumps(reflection, cls=DateTimeEncoder),
            json.dumps(reflection.get("insights", []), cls=DateTimeEncoder)
        )

    async def reset(self):
        """Reset the entire system (use with caution)"""
        logger.warning("Full system reset requested")

        # Clear runtime state
        self.thought_stream.clear()
        self.current_thoughts.clear()
        self.pending_decisions.clear()
        self.attention_focus = None

        # Reset metrics
        self.metrics = {
            "thoughts_processed": 0,
            "decisions_made": 0,
            "goals_completed": 0,
            "learnings_acquired": 0,
            "optimizations_applied": 0,
            "errors_handled": 0,
            "uptime_hours": 0,
            "attention_shifts": 0,
        }

        self.state = ConsciousnessState.AWAKE
        logger.info("System reset complete")

    async def reset_component(self, component: str):
        """Reset a specific component"""
        logger.info(f"Resetting component: {component}")

        if component == "memory" and self.unified_memory:
            self.unified_memory.working_memory.clear()
            self.unified_memory.memory_cache.clear()
        elif component == "neural" and self.neural_network:
            self.neural_network.activation_cache.clear()
        elif component == "thoughts":
            self.thought_stream.clear()
            self.current_thoughts.clear()
        elif component == "decisions":
            self.pending_decisions.clear()
        else:
            logger.warning(f"Unknown component: {component}")

    # =========================================================================
    # SHUTDOWN
    # =========================================================================

    async def shutdown(self):
        """Gracefully shutdown the metacognitive controller"""
        logger.info("Shutting down MetacognitiveController...")

        # Signal shutdown
        self._shutdown_event.set()

        # Wait for background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Persist final state
        await self._persist_state()

        # Close database pool
        if self.db_pool:
            await self.db_pool.close()

        logger.info("MetacognitiveController shutdown complete")


# Singleton instance
_metacognitive_controller: Optional[MetacognitiveController] = None


def get_metacognitive_controller() -> MetacognitiveController:
    """Get the singleton metacognitive controller instance"""
    global _metacognitive_controller
    if _metacognitive_controller is None:
        _metacognitive_controller = MetacognitiveController()
    return _metacognitive_controller


async def initialize_brainops_ai_os(db_pool: Optional[asyncpg.Pool] = None) -> MetacognitiveController:
    """Initialize the complete BrainOps AI OS"""
    controller = get_metacognitive_controller()
    await controller.initialize(db_pool)
    return controller
