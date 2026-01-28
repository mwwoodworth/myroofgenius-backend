"""
BrainOps AI OS - Hierarchical Goal Architecture

Implements a sophisticated goal management system with:
- Strategic goals (long-term vision)
- Tactical objectives (medium-term milestones)
- Operational tasks (immediate actions)
- Goal decomposition and planning
- Progress tracking and adjustment
- Goal conflict resolution
- Priority-based scheduling
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass, field
import asyncpg

from ._resilience import ResilientSubsystem

if TYPE_CHECKING:
    from .metacognitive_controller import MetacognitiveController

logger = logging.getLogger(__name__)


class GoalLevel(str, Enum):
    """Hierarchical levels of goals"""
    STRATEGIC = "strategic"      # Long-term (months/years)
    TACTICAL = "tactical"        # Medium-term (weeks/months)
    OPERATIONAL = "operational"  # Short-term (hours/days)


class GoalStatus(str, Enum):
    """Status of goals"""
    PENDING = "pending"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GoalPriority(str, Enum):
    """Priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Goal:
    """A goal in the hierarchy"""
    id: str
    title: str
    description: str
    level: GoalLevel
    priority: GoalPriority
    status: GoalStatus = GoalStatus.PENDING
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)
    success_criteria: List[Dict[str, Any]] = field(default_factory=list)
    progress: float = 0.0
    deadline: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_agents: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GoalArchitecture(ResilientSubsystem):
    """
    Hierarchical Goal Architecture for BrainOps AI OS

    Provides:
    1. Multi-level goal hierarchy (strategic -> tactical -> operational)
    2. Automatic goal decomposition
    3. Progress tracking and rollup
    4. Dependency management
    5. Conflict resolution
    6. Dynamic prioritization
    """

    def __init__(self, controller: "MetacognitiveController"):
        self.controller = controller
        self.db_pool: Optional[asyncpg.Pool] = None

        # Goal storage
        self.goals: Dict[str, Goal] = {}

        # Priority queue for active goals
        self.priority_queue: List[str] = []

        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown = asyncio.Event()

        # Metrics
        self.metrics = {
            "total_goals": 0,
            "active_goals": 0,
            "completed_goals": 0,
            "failed_goals": 0,
        }

    async def initialize(self, db_pool: asyncpg.Pool):
        """Initialize the goal architecture"""
        self.db_pool = db_pool

        # Create database tables
        await self._initialize_database()

        # Load existing goals
        await self._load_goals()

        # Start background processes
        await self._start_background_processes()

        logger.info(f"GoalArchitecture initialized with {len(self.goals)} goals")

    async def _initialize_database(self):
        """Create required database tables"""
        await self._db_execute_with_retry('''
            -- Goals table
            CREATE TABLE IF NOT EXISTS brainops_goals (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                goal_id VARCHAR(50) UNIQUE NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                level VARCHAR(20) NOT NULL,
                priority VARCHAR(20) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                parent_id VARCHAR(50),
                child_ids TEXT[],
                success_criteria JSONB,
                progress FLOAT DEFAULT 0,
                deadline TIMESTAMP,
                assigned_agents TEXT[],
                dependencies TEXT[],
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_goal_level
                ON brainops_goals(level);
            CREATE INDEX IF NOT EXISTS idx_goal_status
                ON brainops_goals(status);
            CREATE INDEX IF NOT EXISTS idx_goal_priority
                ON brainops_goals(priority);
            CREATE INDEX IF NOT EXISTS idx_goal_parent
                ON brainops_goals(parent_id);

            -- Goal progress history
            CREATE TABLE IF NOT EXISTS brainops_goal_progress (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                goal_id VARCHAR(50) NOT NULL,
                progress FLOAT NOT NULL,
                notes TEXT,
                recorded_at TIMESTAMP DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_progress_goal
                ON brainops_goal_progress(goal_id);

            -- Goal conflicts
            CREATE TABLE IF NOT EXISTS brainops_goal_conflicts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                goal_a VARCHAR(50) NOT NULL,
                goal_b VARCHAR(50) NOT NULL,
                conflict_type VARCHAR(50),
                resolution TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')

    async def _load_goals(self):
        """Load existing goals from database"""
        rows = await self._db_fetch_with_retry('''
            SELECT goal_id, title, description, level, priority, status,
                   parent_id, child_ids, success_criteria, progress,
                   deadline, assigned_agents, dependencies, metadata,
                   created_at, started_at, completed_at
            FROM brainops_goals
            WHERE status NOT IN ('completed', 'cancelled', 'failed')
        ''')

        for row in rows:
            goal = Goal(
                id=row['goal_id'],
                title=row['title'],
                description=row['description'] or "",
                level=GoalLevel(row['level']),
                priority=GoalPriority(row['priority']),
                status=GoalStatus(row['status']),
                parent_id=row['parent_id'],
                child_ids=row['child_ids'] or [],
                success_criteria=row['success_criteria'] or [],
                progress=row['progress'] or 0,
                deadline=row['deadline'],
                assigned_agents=row['assigned_agents'] or [],
                dependencies=row['dependencies'] or [],
                metadata=row['metadata'] or {},
                created_at=row['created_at'],
                started_at=row['started_at'],
                completed_at=row['completed_at'],
            )
            self.goals[goal.id] = goal

        self.metrics["total_goals"] = len(self.goals)
        self.metrics["active_goals"] = sum(
            1 for g in self.goals.values()
            if g.status in [GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS]
        )

        # Build priority queue
        await self._rebuild_priority_queue()

    async def _start_background_processes(self):
        """Start background processes"""
        # Progress monitoring
        self._tasks.append(
            self._create_safe_task(self._progress_monitoring_loop(), name="progress_monitoring")
        )

        # Deadline checking
        self._tasks.append(
            self._create_safe_task(self._deadline_check_loop(), name="deadline_check")
        )

        # Priority rebalancing
        self._tasks.append(
            self._create_safe_task(self._priority_rebalance_loop(), name="priority_rebalance")
        )

        logger.info(f"Started {len(self._tasks)} goal background processes")

    # =========================================================================
    # GOAL CREATION AND MANAGEMENT
    # =========================================================================

    async def create_goal(
        self,
        title: str,
        description: str = "",
        level: GoalLevel = GoalLevel.OPERATIONAL,
        priority: GoalPriority = GoalPriority.MEDIUM,
        parent_id: Optional[str] = None,
        success_criteria: Optional[List[Dict[str, Any]]] = None,
        deadline: Optional[datetime] = None,
        assigned_agents: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new goal"""
        goal_id = str(uuid.uuid4())

        goal = Goal(
            id=goal_id,
            title=title,
            description=description,
            level=level,
            priority=priority,
            parent_id=parent_id,
            success_criteria=success_criteria or [],
            deadline=deadline,
            assigned_agents=assigned_agents or [],
            dependencies=dependencies or [],
            metadata=metadata or {},
        )

        self.goals[goal_id] = goal
        self.metrics["total_goals"] += 1

        # Update parent's children
        if parent_id and parent_id in self.goals:
            self.goals[parent_id].child_ids.append(goal_id)
            await self._update_goal_in_db(self.goals[parent_id])

        # Store in database
        await self._db_execute_with_retry('''
            INSERT INTO brainops_goals
            (goal_id, title, description, level, priority, parent_id,
             success_criteria, deadline, assigned_agents, dependencies, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        ''',
            goal_id, title, description, level.value, priority.value,
            parent_id, json.dumps(success_criteria or []), deadline,
            assigned_agents or [], dependencies or [], json.dumps(metadata or {}))

        # Add to priority queue
        await self._add_to_priority_queue(goal_id)

        return goal_id

    async def update_goal_status(
        self,
        goal_id: str,
        status: GoalStatus,
        notes: str = ""
    ) -> bool:
        """Update goal status"""
        if goal_id not in self.goals:
            return False

        goal = self.goals[goal_id]
        old_status = goal.status
        goal.status = status

        if status == GoalStatus.IN_PROGRESS and not goal.started_at:
            goal.started_at = datetime.now()
            self.metrics["active_goals"] += 1

        elif status == GoalStatus.COMPLETED:
            goal.completed_at = datetime.now()
            goal.progress = 1.0
            self.metrics["completed_goals"] += 1
            self.metrics["active_goals"] = max(0, self.metrics["active_goals"] - 1)

            # Update parent progress
            if goal.parent_id:
                await self._update_parent_progress(goal.parent_id)

        elif status == GoalStatus.FAILED:
            self.metrics["failed_goals"] += 1
            self.metrics["active_goals"] = max(0, self.metrics["active_goals"] - 1)

        await self._update_goal_in_db(goal)

        # Log progress
        await self._db_execute_with_retry('''
            INSERT INTO brainops_goal_progress (goal_id, progress, notes)
            VALUES ($1, $2, $3)
        ''', goal_id, goal.progress, f"Status changed: {old_status.value} -> {status.value}. {notes}")

        return True

    async def update_goal_progress(
        self,
        goal_id: str,
        progress: float,
        notes: str = ""
    ) -> bool:
        """Update goal progress (0-1)"""
        if goal_id not in self.goals:
            return False

        goal = self.goals[goal_id]
        goal.progress = max(0, min(1, progress))

        if progress >= 1.0 and goal.status != GoalStatus.COMPLETED:
            await self.update_goal_status(goal_id, GoalStatus.COMPLETED)

        await self._update_goal_in_db(goal)

        # Log progress
        await self._db_execute_with_retry('''
            INSERT INTO brainops_goal_progress (goal_id, progress, notes)
            VALUES ($1, $2, $3)
        ''', goal_id, progress, notes)

        # Update parent progress
        if goal.parent_id:
            await self._update_parent_progress(goal.parent_id)

        return True

    async def _update_parent_progress(self, parent_id: str):
        """Update parent goal progress based on children"""
        if parent_id not in self.goals:
            return

        parent = self.goals[parent_id]
        if not parent.child_ids:
            return

        # Calculate average progress of children
        child_progress = []
        for child_id in parent.child_ids:
            if child_id in self.goals:
                child_progress.append(self.goals[child_id].progress)

        if child_progress:
            parent.progress = sum(child_progress) / len(child_progress)
            await self._update_goal_in_db(parent)

            # Recursively update grandparent
            if parent.parent_id:
                await self._update_parent_progress(parent.parent_id)

    async def _update_goal_in_db(self, goal: Goal):
        """Update goal in database"""
        await self._db_execute_with_retry('''
            UPDATE brainops_goals
            SET status = $2, progress = $3, child_ids = $4,
                started_at = $5, completed_at = $6
            WHERE goal_id = $1
        ''',
            goal.id, goal.status.value, goal.progress, goal.child_ids,
            goal.started_at, goal.completed_at)

    # =========================================================================
    # GOAL DECOMPOSITION
    # =========================================================================

    async def decompose_goal(
        self,
        goal_id: str,
        subtasks: List[Dict[str, Any]]
    ) -> List[str]:
        """Decompose a goal into subtasks"""
        if goal_id not in self.goals:
            return []

        parent_goal = self.goals[goal_id]
        created_ids = []

        # Determine child level
        if parent_goal.level == GoalLevel.STRATEGIC:
            child_level = GoalLevel.TACTICAL
        elif parent_goal.level == GoalLevel.TACTICAL:
            child_level = GoalLevel.OPERATIONAL
        else:
            child_level = GoalLevel.OPERATIONAL

        for subtask in subtasks:
            child_id = await self.create_goal(
                title=subtask.get('title', 'Subtask'),
                description=subtask.get('description', ''),
                level=child_level,
                priority=GoalPriority(subtask.get('priority', parent_goal.priority.value)),
                parent_id=goal_id,
                success_criteria=subtask.get('success_criteria', []),
                deadline=subtask.get('deadline'),
                assigned_agents=subtask.get('agents', []),
                dependencies=subtask.get('dependencies', []),
            )
            created_ids.append(child_id)

        return created_ids

    async def auto_decompose_goal(self, goal_id: str) -> List[str]:
        """Automatically decompose a goal using AI"""
        if goal_id not in self.goals:
            return []

        goal = self.goals[goal_id]

        # Use reasoning engine if available
        if self.controller and self.controller.reasoning_engine:
            subtasks = await self.controller.reasoning_engine.decompose_goal(goal)
            if subtasks:
                return await self.decompose_goal(goal_id, subtasks)

        return []

    # =========================================================================
    # PRIORITY MANAGEMENT
    # =========================================================================

    async def _rebuild_priority_queue(self):
        """Rebuild the priority queue based on current goals"""
        active_goals = [
            g for g in self.goals.values()
            if g.status in [GoalStatus.PENDING, GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS]
        ]

        # Sort by priority, then by deadline, then by level
        priority_order = {
            GoalPriority.CRITICAL: 0,
            GoalPriority.HIGH: 1,
            GoalPriority.MEDIUM: 2,
            GoalPriority.LOW: 3,
        }

        level_order = {
            GoalLevel.OPERATIONAL: 0,  # Operational first (immediate)
            GoalLevel.TACTICAL: 1,
            GoalLevel.STRATEGIC: 2,
        }

        sorted_goals = sorted(
            active_goals,
            key=lambda g: (
                priority_order.get(g.priority, 2),
                g.deadline or datetime.max,
                level_order.get(g.level, 1),
            )
        )

        self.priority_queue = [g.id for g in sorted_goals]

    async def _add_to_priority_queue(self, goal_id: str):
        """Add a goal to the priority queue in correct position"""
        self.priority_queue.append(goal_id)
        await self._rebuild_priority_queue()

    async def get_next_goal(self) -> Optional[Goal]:
        """Get the next highest priority goal to work on"""
        for goal_id in self.priority_queue:
            goal = self.goals.get(goal_id)
            if goal and goal.status in [GoalStatus.PENDING, GoalStatus.ACTIVE]:
                # Check dependencies
                deps_met = all(
                    self.goals.get(dep_id, Goal(id='', title='', description='', level=GoalLevel.OPERATIONAL, priority=GoalPriority.LOW)).status == GoalStatus.COMPLETED
                    for dep_id in goal.dependencies
                    if dep_id in self.goals
                )

                if deps_met:
                    return goal

        return None

    async def get_priority_items(self) -> List[Dict[str, Any]]:
        """Get prioritized list of items for attention management"""
        items = []

        for goal_id in self.priority_queue[:10]:  # Top 10
            goal = self.goals.get(goal_id)
            if goal:
                priority_num = {
                    GoalPriority.CRITICAL: 0,
                    GoalPriority.HIGH: 1,
                    GoalPriority.MEDIUM: 2,
                    GoalPriority.LOW: 3,
                }.get(goal.priority, 2)

                items.append({
                    "id": goal.id,
                    "description": goal.title,
                    "priority": priority_num,
                    "urgency": 1.0 if goal.deadline and goal.deadline < datetime.now() + timedelta(days=1) else 0.5,
                    "type": "goal",
                })

        return items

    # =========================================================================
    # BACKGROUND PROCESSES
    # =========================================================================

    async def _progress_monitoring_loop(self):
        """Monitor goal progress"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                # Check for stalled goals
                for goal in self.goals.values():
                    if goal.status == GoalStatus.IN_PROGRESS:
                        # Check if progress has stalled
                        recent_progress = await self._db_fetchval_with_retry('''
                            SELECT progress FROM brainops_goal_progress
                            WHERE goal_id = $1
                            ORDER BY recorded_at DESC
                            LIMIT 1
                        ''', goal.id)

                        if recent_progress is not None and abs(goal.progress - recent_progress) < 0.01:
                            # Progress stalled - might need attention
                            logger.info(f"Goal {goal.id} progress stalled at {goal.progress:.1%}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Progress monitoring error: {e}")
                await asyncio.sleep(300)

    async def _deadline_check_loop(self):
        """Check for approaching deadlines"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(3600)  # Every hour

                now = datetime.now()
                for goal in self.goals.values():
                    if goal.deadline and goal.status not in [GoalStatus.COMPLETED, GoalStatus.CANCELLED]:
                        time_remaining = goal.deadline - now

                        if time_remaining < timedelta(hours=0):
                            # Deadline passed
                            logger.warning(f"Goal {goal.id} deadline passed!")
                            if self.controller:
                                from .metacognitive_controller import AttentionPriority
                                await self.controller._record_thought({
                                    "type": "deadline_passed",
                                    "goal_id": goal.id,
                                    "title": goal.title,
                                }, AttentionPriority.URGENT, "goal_architecture")

                        elif time_remaining < timedelta(days=1):
                            # Deadline approaching
                            logger.info(f"Goal {goal.id} deadline in {time_remaining}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Deadline check error: {e}")
                await asyncio.sleep(3600)

    async def _priority_rebalance_loop(self):
        """Periodically rebalance priorities"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(1800)  # Every 30 minutes

                await self._rebuild_priority_queue()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Priority rebalance error: {e}")
                await asyncio.sleep(1800)

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def process_goal_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Process a goal update from the controller"""
        action = update.get("action", "status")

        if action == "create":
            goal_id = await self.create_goal(
                title=update.get("title", "New Goal"),
                description=update.get("description", ""),
                level=GoalLevel(update.get("level", "operational")),
                priority=GoalPriority(update.get("priority", "medium")),
            )
            return {"status": "created", "goal_id": goal_id}

        elif action == "update_status":
            success = await self.update_goal_status(
                update.get("goal_id"),
                GoalStatus(update.get("status", "active")),
                update.get("notes", ""),
            )
            return {"status": "updated" if success else "failed"}

        elif action == "update_progress":
            success = await self.update_goal_progress(
                update.get("goal_id"),
                update.get("progress", 0),
                update.get("notes", ""),
            )
            return {"status": "updated" if success else "failed"}

        return {"status": "unknown_action"}

    async def get_active_goals(self) -> List[Dict[str, Any]]:
        """Get all active goals"""
        return [
            {
                "id": g.id,
                "title": g.title,
                "level": g.level.value,
                "priority": g.priority.value,
                "status": g.status.value,
                "progress": g.progress,
                "deadline": g.deadline.isoformat() if g.deadline else None,
            }
            for g in self.goals.values()
            if g.status in [GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS, GoalStatus.PENDING]
        ]

    async def get_health(self) -> Dict[str, Any]:
        """Get goal architecture health"""
        active_tasks = sum(1 for t in self._tasks if not t.done())

        return {
            "status": "healthy" if active_tasks == len(self._tasks) else "degraded",
            "score": active_tasks / len(self._tasks) if self._tasks else 1.0,
            "total_goals": len(self.goals),
            "active_goals": self.metrics["active_goals"],
            "completed_goals": self.metrics["completed_goals"],
            "metrics": self.metrics.copy(),
        }

    async def shutdown(self):
        """Shutdown the goal architecture"""
        self._shutdown.set()

        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("GoalArchitecture shutdown complete")


# Singleton
_goal_architecture: Optional[GoalArchitecture] = None


def get_goal_architecture() -> Optional[GoalArchitecture]:
    """Get the goal architecture instance"""
    return _goal_architecture
