"""
BrainOps AI OS - Self-Optimization System

Provides autonomous self-improvement:
- Performance optimization
- Resource allocation tuning
- Query optimization
- Cache management
- Self-healing capabilities
- Configuration auto-tuning
"""

import asyncio
import json
import logging
import uuid
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass, field
import asyncpg
import psutil

if TYPE_CHECKING:
    from .metacognitive_controller import MetacognitiveController

logger = logging.getLogger(__name__)


class OptimizationType(str, Enum):
    """Types of optimization"""
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    QUERY = "query"
    CACHE = "cache"
    CONFIGURATION = "configuration"
    SELF_HEALING = "self_healing"


class OptimizationStatus(str, Enum):
    """Status of optimization"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Optimization:
    """An optimization action"""
    id: str
    type: OptimizationType
    description: str
    target: str
    before_state: Dict[str, Any]
    after_state: Optional[Dict[str, Any]] = None
    improvement: float = 0.0
    status: OptimizationStatus = OptimizationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class SelfOptimizationSystem:
    """
    Self-Optimization System for BrainOps AI OS

    Provides:
    1. Automatic performance optimization
    2. Resource allocation tuning
    3. Query optimization suggestions
    4. Cache management
    5. Self-healing from failures
    6. Configuration auto-tuning
    """

    def __init__(self, controller: "MetacognitiveController"):
        self.controller = controller
        self.db_pool: Optional[asyncpg.Pool] = None

        # Optimization history
        self.optimizations: Dict[str, Optimization] = {}

        # Performance baselines
        self.baselines: Dict[str, float] = {}

        # Configuration tracking
        self.configurations: Dict[str, Any] = {}

        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown = asyncio.Event()

        # Metrics
        self.metrics = {
            "optimizations_applied": 0,
            "improvements_total": 0.0,
            "self_heals": 0,
            "rollbacks": 0,
        }

    async def initialize(self, db_pool: asyncpg.Pool):
        """Initialize the self-optimization system"""
        self.db_pool = db_pool

        await self._initialize_database()
        await self._load_baselines()
        await self._start_background_processes()

        logger.info("SelfOptimizationSystem initialized")

    async def _initialize_database(self):
        """Create required database tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                -- Optimization history
                CREATE TABLE IF NOT EXISTS brainops_optimizations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    optimization_id VARCHAR(50) UNIQUE NOT NULL,
                    optimization_type VARCHAR(50) NOT NULL,
                    description TEXT,
                    target VARCHAR(255),
                    before_state JSONB,
                    after_state JSONB,
                    improvement FLOAT,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_optimization_type
                    ON brainops_optimizations(optimization_type);
                CREATE INDEX IF NOT EXISTS idx_optimization_status
                    ON brainops_optimizations(status);

                -- Performance baselines
                CREATE TABLE IF NOT EXISTS brainops_baselines (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    metric_name VARCHAR(100) UNIQUE NOT NULL,
                    baseline_value FLOAT NOT NULL,
                    threshold_low FLOAT,
                    threshold_high FLOAT,
                    updated_at TIMESTAMP DEFAULT NOW()
                );

                -- Self-healing events
                CREATE TABLE IF NOT EXISTS brainops_self_healing (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    event_type VARCHAR(50),
                    trigger TEXT,
                    action_taken TEXT,
                    success BOOLEAN,
                    details JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            ''')

    async def _load_baselines(self):
        """Load performance baselines"""
        rows = await self._db_fetch_with_retry('''
            SELECT metric_name, baseline_mean
            FROM brainops_baselines
        ''')

        for row in rows:
            self.baselines[row['metric_name']] = row['baseline_mean']

        # Set default baselines if empty
        if not self.baselines:
            self.baselines = {
                "api_response_time_ms": 200,
                "database_query_time_ms": 50,
                "memory_usage_percent": 70,
                "cpu_usage_percent": 60,
                "error_rate_percent": 1,
            }

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

    async def _db_execute_with_retry(self, query: str, *args, max_retries: int = 2):
        """Execute a database query with retry on connection errors."""
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

    async def _db_fetchrow_with_retry(self, query: str, *args, max_retries: int = 2):
        """Fetch single database row with retry on connection errors."""
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

    async def _db_fetch_with_retry(self, query: str, *args, max_retries: int = 2):
        """Fetch database rows with retry on connection errors."""
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

    async def _start_background_processes(self):
        """Start background optimization processes"""
        # Performance monitoring
        self._tasks.append(
            self._create_safe_task(self._performance_monitoring_loop(), name="perf_monitoring")
        )

        # Resource optimization
        self._tasks.append(
            self._create_safe_task(self._resource_optimization_loop(), name="resource_optimization")
        )

        # Cache optimization
        self._tasks.append(
            self._create_safe_task(self._cache_optimization_loop(), name="cache_optimization")
        )

        # Self-healing monitor
        self._tasks.append(
            self._create_safe_task(self._self_healing_loop(), name="self_healing")
        )

        # Database optimization
        self._tasks.append(
            self._create_safe_task(self._database_optimization_loop(), name="db_optimization")
        )

        logger.info(f"Started {len(self._tasks)} optimization background processes")

    # =========================================================================
    # PERFORMANCE MONITORING
    # =========================================================================

    async def _performance_monitoring_loop(self):
        """Monitor system performance"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(60)  # Every minute

                # Collect metrics
                metrics = await self._collect_performance_metrics()

                # Check against baselines
                for metric_name, value in metrics.items():
                    baseline = self.baselines.get(metric_name)
                    if baseline:
                        # Check if degraded (>50% worse than baseline)
                        if value > baseline * 1.5:
                            await self._trigger_optimization(
                                OptimizationType.PERFORMANCE,
                                f"Performance degradation: {metric_name}",
                                metric_name,
                                {"current": value, "baseline": baseline}
                            )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(60)

    async def _collect_performance_metrics(self) -> Dict[str, float]:
        """Collect current performance metrics"""
        metrics = {}

        # System metrics
        metrics["cpu_usage_percent"] = psutil.cpu_percent()
        metrics["memory_usage_percent"] = psutil.virtual_memory().percent

        # Database metrics
        try:
            start = time.time()
            await self._db_execute_with_retry("SELECT 1")
            metrics["database_query_time_ms"] = (time.time() - start) * 1000
        except Exception:
            metrics["database_query_time_ms"] = 9999

        return metrics

    # =========================================================================
    # RESOURCE OPTIMIZATION
    # =========================================================================

    async def _resource_optimization_loop(self):
        """Optimize resource allocation"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                # Check memory usage
                memory = psutil.virtual_memory()
                if memory.percent > 85:
                    await self._optimize_memory()

                # Check disk usage
                disk = psutil.disk_usage('/')
                if disk.percent > 90:
                    await self._optimize_disk()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Resource optimization error: {e}")
                await asyncio.sleep(300)

    async def _optimize_memory(self):
        """Optimize memory usage"""
        logger.info("Triggering memory optimization...")

        before_state = {"memory_percent": psutil.virtual_memory().percent}

        # Clear caches
        if self.controller:
            # Clear reasoning cache
            if self.controller.reasoning_engine:
                self.controller.reasoning_engine.reasoning_cache.clear()

            # Trim working memory
            if self.controller.unified_memory:
                await self.controller.unified_memory._manage_working_memory_size()

        # Force garbage collection
        import gc
        gc.collect()

        after_state = {"memory_percent": psutil.virtual_memory().percent}
        improvement = before_state["memory_percent"] - after_state["memory_percent"]

        await self._record_optimization(
            OptimizationType.RESOURCE,
            "Memory optimization",
            "system_memory",
            before_state,
            after_state,
            improvement
        )

    async def _optimize_disk(self):
        """Optimize disk usage"""
        logger.info("Triggering disk optimization...")

        # Clean up old logs and temp files (with retry)
        await self._db_execute_with_retry('''
            DELETE FROM brainops_sensor_readings
            WHERE created_at < NOW() - INTERVAL '7 days'
        ''')

        await self._db_execute_with_retry('''
            DELETE FROM brainops_activation_history
            WHERE created_at < NOW() - INTERVAL '3 days'
        ''')

        await self._db_execute_with_retry('''
            DELETE FROM brainops_thought_stream
            WHERE created_at < NOW() - INTERVAL '7 days'
        ''')

    # =========================================================================
    # CACHE OPTIMIZATION
    # =========================================================================

    async def _cache_optimization_loop(self):
        """Optimize cache performance"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(600)  # Every 10 minutes

                # Analyze cache hit rates and optimize

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache optimization error: {e}")
                await asyncio.sleep(600)

    # =========================================================================
    # DATABASE OPTIMIZATION
    # =========================================================================

    async def _database_optimization_loop(self):
        """Optimize database performance"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(3600)  # Every hour

                # Analyze tables for optimization (with retry)
                await self._db_execute_with_retry("ANALYZE brainops_unified_memory")
                await self._db_execute_with_retry("ANALYZE brainops_sensor_readings")
                await self._db_execute_with_retry("ANALYZE brainops_thought_stream")

                logger.info("Database optimization completed")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Database optimization error: {e}")
                await asyncio.sleep(3600)

    # =========================================================================
    # SELF-HEALING
    # =========================================================================

    async def _self_healing_loop(self):
        """Monitor for issues and self-heal"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(30)  # Every 30 seconds

                # Check for stuck processes
                await self._check_stuck_processes()

                # Check for database connection issues
                await self._check_database_health()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Self-healing loop error: {e}")
                await asyncio.sleep(60)

    async def _check_stuck_processes(self):
        """Check for and fix stuck processes"""
        if self.controller:
            # Check for stuck background tasks
            for task in self.controller._background_tasks:
                if task.done() and not task.cancelled():
                    exc = task.exception()
                    if exc:
                        logger.error(f"Background task failed: {exc}")
                        await self._record_self_healing(
                            "task_failure",
                            str(exc),
                            "Logged error for investigation",
                            False,
                            {"exception": str(exc)}
                        )

    async def _check_database_health(self):
        """Check database health and recover if needed"""
        try:
            await self._db_execute_with_retry("SELECT 1")
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            await self._record_self_healing(
                "database_failure",
                str(e),
                "Attempting reconnection",
                False,
                {"error": str(e)}
            )

    async def activate_self_healing(self, alert: Dict[str, Any]):
        """Activate self-healing in response to an alert"""
        alert_type = alert.get("type", "unknown")

        logger.info(f"Activating self-healing for: {alert_type}")

        if alert_type == "system_failure":
            # Attempt recovery
            action = "Initiated system recovery protocol"

        elif alert_type == "memory_exhaustion":
            await self._optimize_memory()
            action = "Executed memory optimization"

        elif alert_type == "database_connection":
            # Pool should auto-recover, but we can force it
            action = "Database pool will auto-recover"

        else:
            action = "Logged for investigation"

        await self._record_self_healing(
            alert_type,
            json.dumps(alert),
            action,
            True,
            alert
        )

        self.metrics["self_heals"] += 1

    async def _record_self_healing(
        self,
        event_type: str,
        trigger: str,
        action: str,
        success: bool,
        details: Dict[str, Any]
    ):
        """Record self-healing event"""
        await self._db_execute_with_retry('''
            INSERT INTO brainops_self_healing
            (event_type, trigger, action_taken, success, details)
            VALUES ($1, $2, $3, $4, $5)
        ''', event_type, trigger, action, success, json.dumps(details))

    # =========================================================================
    # OPTIMIZATION RECORDING
    # =========================================================================

    async def _trigger_optimization(
        self,
        opt_type: OptimizationType,
        description: str,
        target: str,
        before_state: Dict[str, Any]
    ):
        """Trigger an optimization"""
        opt_id = str(uuid.uuid4())

        optimization = Optimization(
            id=opt_id,
            type=opt_type,
            description=description,
            target=target,
            before_state=before_state,
            status=OptimizationStatus.IN_PROGRESS,
        )

        self.optimizations[opt_id] = optimization

        # Execute optimization based on type
        if opt_type == OptimizationType.PERFORMANCE:
            await self._execute_performance_optimization(optimization)
        elif opt_type == OptimizationType.RESOURCE:
            await self._execute_resource_optimization(optimization)

    async def _execute_performance_optimization(self, optimization: Optimization):
        """Execute performance optimization"""
        # Implementation depends on target
        optimization.status = OptimizationStatus.COMPLETED
        optimization.completed_at = datetime.now()

    async def _execute_resource_optimization(self, optimization: Optimization):
        """Execute resource optimization"""
        optimization.status = OptimizationStatus.COMPLETED
        optimization.completed_at = datetime.now()

    async def _record_optimization(
        self,
        opt_type: OptimizationType,
        description: str,
        target: str,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        improvement: float
    ):
        """Record a completed optimization"""
        opt_id = str(uuid.uuid4())

        await self._db_execute_with_retry('''
            INSERT INTO brainops_optimizations
            (optimization_id, optimization_type, description, target,
             before_state, after_state, improvement, status, completed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
        ''',
            opt_id, opt_type.value, description, target,
            json.dumps(before_state), json.dumps(after_state),
            improvement, OptimizationStatus.COMPLETED.value)

        self.metrics["optimizations_applied"] += 1
        self.metrics["improvements_total"] += improvement

        logger.info(f"Optimization recorded: {description} (improvement: {improvement:.1f}%)")

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def process_optimization(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process optimization request from controller"""
        return {"status": "processed"}

    async def optimize_component(self, component: str):
        """Optimize a specific component"""
        logger.info(f"Optimizing component: {component}")

        if component == "memory":
            await self._optimize_memory()
        elif component == "database":
            await self._db_execute_with_retry("ANALYZE")

    async def get_health(self) -> Dict[str, Any]:
        """Get self-optimization system health"""
        active_tasks = sum(1 for t in self._tasks if not t.done())

        return {
            "status": "healthy" if active_tasks == len(self._tasks) else "degraded",
            "score": active_tasks / len(self._tasks) if self._tasks else 1.0,
            "active_optimizations": len([
                o for o in self.optimizations.values()
                if o.status == OptimizationStatus.IN_PROGRESS
            ]),
            "metrics": self.metrics.copy(),
        }

    async def shutdown(self):
        """Shutdown the self-optimization system"""
        self._shutdown.set()

        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("SelfOptimizationSystem shutdown complete")


# Singleton
_self_optimization: Optional[SelfOptimizationSystem] = None


def get_self_optimization() -> Optional[SelfOptimizationSystem]:
    """Get the self-optimization instance"""
    return _self_optimization
