"""
BrainOps AI OS - Dynamic Neural Network System

Implements true neural network dynamics with:
- Hebbian learning ("neurons that fire together wire together")
- Dynamic pathway strengthening/weakening
- Agent specialization and collaboration
- Emergent behavior detection
- Neural activity monitoring
- Attention-based routing
"""

import asyncio
import json
import logging
import os
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import asyncpg
import numpy as np

from ._resilience import ResilientSubsystem

if TYPE_CHECKING:
    from .metacognitive_controller import MetacognitiveController

logger = logging.getLogger(__name__)


class NeuronType(str, Enum):
    """Types of neurons in the network"""

    SENSORY = "sensory"  # Input processing
    MOTOR = "motor"  # Output/action
    INTERNEURON = "interneuron"  # Internal processing
    MODULATORY = "modulatory"  # Modifies other neurons


class PathwayState(str, Enum):
    """States of neural pathways"""

    ACTIVE = "active"
    POTENTIATED = "potentiated"  # Recently strengthened
    DEPRESSED = "depressed"  # Recently weakened
    DORMANT = "dormant"  # Rarely used


@dataclass
class Neuron:
    """A neuron in the dynamic network"""

    id: str
    name: str
    neuron_type: NeuronType
    agent_id: Optional[str] = None  # Associated AI agent
    activation: float = 0.0  # Current activation level
    threshold: float = 0.5  # Activation threshold
    bias: float = 0.0
    input_weights: Dict[str, float] = field(default_factory=dict)
    output_connections: Set[str] = field(default_factory=set)
    last_fired: Optional[datetime] = None
    fire_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Synapse:
    """A connection between neurons"""

    id: str
    source_id: str
    target_id: str
    weight: float = 0.5
    plasticity: float = 0.1  # Learning rate
    last_active: Optional[datetime] = None
    co_activation_count: int = 0
    state: PathwayState = PathwayState.ACTIVE


@dataclass
class NeuralCluster:
    """A cluster of related neurons"""

    id: str
    name: str
    neuron_ids: Set[str]
    specialization: str
    activation_pattern: List[float] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class DynamicNeuralNetwork(ResilientSubsystem):
    """
    Dynamic Neural Network for BrainOps AI OS

    Implements:
    1. Hebbian learning for pathway strengthening
    2. Spike-timing dependent plasticity (STDP)
    3. Dynamic agent routing based on specialization
    4. Emergent cluster detection
    5. Attention-based activation
    """

    def __init__(self, controller: "MetacognitiveController"):
        self.controller = controller
        self.db_pool: Optional[asyncpg.Pool] = None

        # Network structure
        self.neurons: Dict[str, Neuron] = {}
        self.synapses: Dict[str, Synapse] = {}
        self.clusters: Dict[str, NeuralCluster] = {}

        # Activity tracking
        self.activation_history: deque = deque(maxlen=10000)
        self.co_activation_matrix: Dict[Tuple[str, str], int] = defaultdict(int)

        # Learning parameters
        self.learning_rate = 0.1
        self.decay_rate = 0.001
        self.potentiation_threshold = 0.7
        self.depression_threshold = 0.3

        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown = asyncio.Event()

        # Metrics
        self.metrics = {
            "total_neurons": 0,
            "total_synapses": 0,
            "total_activations": 0,
            "pathways_potentiated": 0,
            "pathways_depressed": 0,
            "emergent_clusters": 0,
        }

    async def initialize(self, db_pool: asyncpg.Pool):
        """Initialize the neural network"""
        self.db_pool = db_pool

        # Create database tables
        try:
            await self._initialize_database()
        except RuntimeError as e:
            if "BLOCKED_RUNTIME_DDL" in str(e):
                logger.info("DDL kill-switch active — skipping runtime table creation")
            else:
                raise
        except Exception as e:
            if "permission denied" in str(e).lower():
                pass
            else:
                raise

        # Load existing network
        await self._load_network()

        # Create default neurons for agents
        await self._initialize_agent_neurons()

        # Start background processes
        await self._start_background_processes()

        logger.info(
            f"DynamicNeuralNetwork initialized with {len(self.neurons)} neurons, {len(self.synapses)} synapses"
        )

    async def _initialize_database(self):
        """Create required database tables"""
        await self._db_execute_with_retry(
            """
            -- Neurons table
            CREATE TABLE IF NOT EXISTS brainops_neurons (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                neuron_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                neuron_type VARCHAR(20) NOT NULL,
                agent_id VARCHAR(50),
                threshold FLOAT DEFAULT 0.5,
                bias FLOAT DEFAULT 0.0,
                fire_count INT DEFAULT 0,
                last_fired TIMESTAMP,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_neuron_type
                ON brainops_neurons(neuron_type);
            CREATE INDEX IF NOT EXISTS idx_neuron_agent
                ON brainops_neurons(agent_id);

            -- Synapses table
            CREATE TABLE IF NOT EXISTS brainops_synapses (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                synapse_id VARCHAR(50) UNIQUE NOT NULL,
                source_id VARCHAR(50) NOT NULL,
                target_id VARCHAR(50) NOT NULL,
                weight FLOAT DEFAULT 0.5,
                plasticity FLOAT DEFAULT 0.1,
                co_activation_count INT DEFAULT 0,
                state VARCHAR(20) DEFAULT 'active',
                last_active TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(source_id, target_id)
            );

            CREATE INDEX IF NOT EXISTS idx_synapse_source
                ON brainops_synapses(source_id);
            CREATE INDEX IF NOT EXISTS idx_synapse_target
                ON brainops_synapses(target_id);
            CREATE INDEX IF NOT EXISTS idx_synapse_weight
                ON brainops_synapses(weight DESC);

            -- Neural clusters table
            CREATE TABLE IF NOT EXISTS brainops_neural_clusters (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                cluster_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                neuron_ids TEXT[] NOT NULL,
                specialization VARCHAR(100),
                activation_pattern FLOAT[],
                created_at TIMESTAMP DEFAULT NOW()
            );

            -- Activation history
            CREATE TABLE IF NOT EXISTS brainops_activation_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                neuron_id VARCHAR(50) NOT NULL,
                activation_level FLOAT NOT NULL,
                trigger_source VARCHAR(100),
                propagated_to TEXT[],
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_activation_neuron
                ON brainops_activation_history(neuron_id);
            CREATE INDEX IF NOT EXISTS idx_activation_time
                ON brainops_activation_history(created_at DESC);

            -- Co-activation tracking for Hebbian learning
            CREATE TABLE IF NOT EXISTS brainops_co_activations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                neuron_a VARCHAR(50) NOT NULL,
                neuron_b VARCHAR(50) NOT NULL,
                count INT DEFAULT 1,
                last_co_activation TIMESTAMP DEFAULT NOW(),
                UNIQUE(neuron_a, neuron_b)
            );
        """
        )

    async def _load_network(self):
        """Load existing network from database"""
        # Load neurons
        neurons = await self._db_fetch_with_retry(
            """
            SELECT neuron_id, name, neuron_type, agent_id, threshold,
                   bias, fire_count, last_fired, metadata
            FROM brainops_neurons
        """
        )

        for row in neurons:
            neuron = Neuron(
                id=row["neuron_id"],
                name=row["name"],
                neuron_type=NeuronType(row["neuron_type"]),
                agent_id=row["agent_id"],
                threshold=row["threshold"],
                bias=row["bias"],
                fire_count=row["fire_count"],
                last_fired=row["last_fired"],
                metadata=row["metadata"] or {},
            )
            self.neurons[neuron.id] = neuron

        # Load synapses
        synapses = await self._db_fetch_with_retry(
            """
            SELECT synapse_id, source_id, target_id, weight,
                   plasticity, co_activation_count, state, last_active
            FROM brainops_synapses
        """
        )

        for row in synapses:
            synapse = Synapse(
                id=row["synapse_id"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                weight=row["weight"],
                plasticity=row["plasticity"],
                co_activation_count=row["co_activation_count"],
                state=PathwayState(row["state"]),
                last_active=row["last_active"],
            )
            self.synapses[synapse.id] = synapse

            # Update neuron connections
            if synapse.source_id in self.neurons:
                self.neurons[synapse.source_id].output_connections.add(
                    synapse.target_id
                )
            if synapse.target_id in self.neurons:
                self.neurons[synapse.target_id].input_weights[
                    synapse.source_id
                ] = synapse.weight

        # Load clusters
        clusters = await self._db_fetch_with_retry(
            """
            SELECT cluster_id, name, neuron_ids, specialization
            FROM brainops_neural_clusters
        """
        )

        for row in clusters:
            cluster = NeuralCluster(
                id=row["cluster_id"],
                name=row["name"],
                neuron_ids=set(row["neuron_ids"] or []),
                specialization=row["specialization"],
            )
            self.clusters[cluster.id] = cluster

        self.metrics["total_neurons"] = len(self.neurons)
        self.metrics["total_synapses"] = len(self.synapses)

    async def _initialize_agent_neurons(self):
        """Create neurons for registered AI agents"""
        if not self.controller:
            return

        for agent_id, agent in self.controller.agents.items():
            neuron_id = f"agent_{agent_id}"

            if neuron_id not in self.neurons:
                await self.create_neuron(
                    name=agent.get("name", agent_id),
                    neuron_type=NeuronType.INTERNEURON,
                    agent_id=agent_id,
                    metadata={
                        "capabilities": agent.get("capabilities", []),
                        "type": agent.get("type", "general"),
                    },
                )

    async def _start_background_processes(self):
        """Start background neural processes"""
        # Hebbian learning update
        self._tasks.append(
            self._create_safe_task(
                self._hebbian_learning_loop(), name="hebbian_learning"
            )
        )

        # Synaptic decay
        self._tasks.append(
            self._create_safe_task(self._synaptic_decay_loop(), name="synaptic_decay")
        )

        # Cluster detection
        self._tasks.append(
            self._create_safe_task(
                self._cluster_detection_loop(), name="cluster_detection"
            )
        )

        # Activity monitoring
        self._tasks.append(
            self._create_safe_task(
                self._activity_monitoring_loop(), name="activity_monitoring"
            )
        )

        logger.info(f"Started {len(self._tasks)} neural background processes")

    # =========================================================================
    # NEURON OPERATIONS
    # =========================================================================

    async def create_neuron(
        self,
        name: str,
        neuron_type: NeuronType,
        agent_id: Optional[str] = None,
        threshold: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new neuron"""
        neuron_id = str(uuid.uuid4())

        neuron = Neuron(
            id=neuron_id,
            name=name,
            neuron_type=neuron_type,
            agent_id=agent_id,
            threshold=threshold,
            metadata=metadata or {},
        )

        self.neurons[neuron_id] = neuron
        self.metrics["total_neurons"] += 1

        # Persist to database
        await self._db_execute_with_retry(
            """
            INSERT INTO brainops_neurons
            (neuron_id, name, neuron_type, agent_id, threshold, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
        """,
            neuron_id,
            name,
            neuron_type.value,
            agent_id,
            threshold,
            json.dumps(metadata or {}),
        )

        return neuron_id

    async def create_synapse(
        self,
        source_id: str,
        target_id: str,
        weight: float = 0.5,
        plasticity: float = 0.1,
    ) -> Optional[str]:
        """Create a synapse between two neurons"""
        if source_id not in self.neurons or target_id not in self.neurons:
            return None

        synapse_id = str(uuid.uuid4())

        synapse = Synapse(
            id=synapse_id,
            source_id=source_id,
            target_id=target_id,
            weight=weight,
            plasticity=plasticity,
        )

        self.synapses[synapse_id] = synapse
        self.neurons[source_id].output_connections.add(target_id)
        self.neurons[target_id].input_weights[source_id] = weight
        self.metrics["total_synapses"] += 1

        # Persist to database
        await self._db_execute_with_retry(
            """
            INSERT INTO brainops_synapses
            (synapse_id, source_id, target_id, weight, plasticity)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (source_id, target_id) DO UPDATE SET
                weight = EXCLUDED.weight
        """,
            synapse_id,
            source_id,
            target_id,
            weight,
            plasticity,
        )

        return synapse_id

    async def activate_neuron(
        self, neuron_id: str, input_value: float, source: str = "external"
    ) -> Dict[str, Any]:
        """
        Activate a neuron and propagate through the network.

        Args:
            neuron_id: Neuron to activate
            input_value: Activation input (0-1)
            source: Source of activation

        Returns:
            Activation result with propagation info
        """
        if neuron_id not in self.neurons:
            return {"status": "neuron_not_found"}

        neuron = self.neurons[neuron_id]
        now = datetime.now()

        # Calculate activation using sigmoid-like function
        weighted_input = input_value + neuron.bias
        for source_id, weight in neuron.input_weights.items():
            if source_id in self.neurons:
                weighted_input += self.neurons[source_id].activation * weight

        # Apply activation function
        activation = 1.0 / (1.0 + np.exp(-weighted_input))
        neuron.activation = activation

        propagated_to = []

        # Check if neuron fires (exceeds threshold)
        if activation > neuron.threshold:
            neuron.last_fired = now
            neuron.fire_count += 1

            # Propagate to connected neurons
            for target_id in neuron.output_connections:
                if target_id in self.neurons:
                    # Get synapse weight
                    synapse_key = f"{neuron_id}_{target_id}"
                    synapse = next(
                        (
                            s
                            for s in self.synapses.values()
                            if s.source_id == neuron_id and s.target_id == target_id
                        ),
                        None,
                    )

                    if synapse:
                        # Propagate activation
                        propagated_activation = activation * synapse.weight
                        await self.activate_neuron(
                            target_id, propagated_activation, source=neuron_id
                        )
                        propagated_to.append(target_id)

                        # Record co-activation for Hebbian learning
                        self.co_activation_matrix[(neuron_id, target_id)] += 1
                        synapse.co_activation_count += 1
                        synapse.last_active = now

        self.metrics["total_activations"] += 1

        # Record activation
        self.activation_history.append(
            {
                "neuron_id": neuron_id,
                "activation": activation,
                "source": source,
                "propagated_to": propagated_to,
                "timestamp": now,
            }
        )

        # Store in database
        await self._db_execute_with_retry(
            """
            INSERT INTO brainops_activation_history
            (neuron_id, activation_level, trigger_source, propagated_to)
            VALUES ($1, $2, $3, $4)
        """,
            neuron_id,
            activation,
            source,
            propagated_to,
        )

        # Update neuron stats
        await self._db_execute_with_retry(
            """
            UPDATE brainops_neurons
            SET fire_count = $2, last_fired = $3
            WHERE neuron_id = $1
        """,
            neuron_id,
            neuron.fire_count,
            neuron.last_fired,
        )

        return {
            "status": "activated",
            "neuron_id": neuron_id,
            "activation": activation,
            "fired": activation > neuron.threshold,
            "propagated_to": propagated_to,
        }

    # =========================================================================
    # HEBBIAN LEARNING
    # =========================================================================

    async def _hebbian_learning_loop(self):
        """Apply Hebbian learning to strengthen/weaken synapses"""
        while not self._shutdown.is_set():
            try:
                # Run every 5 minutes
                await asyncio.sleep(300)

                await self._apply_hebbian_learning()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Hebbian learning error: {e}")
                await asyncio.sleep(300)

    async def _apply_hebbian_learning(self):
        """Apply Hebbian learning rules to all synapses"""
        logger.info("Applying Hebbian learning...")

        # Get recent co-activations
        co_activations = await self._db_fetch_with_retry(
            """
            SELECT neuron_a, neuron_b, count
            FROM brainops_co_activations
            WHERE last_co_activation > NOW() - INTERVAL '1 hour'
        """
        )

        for row in co_activations:
            source_id = row["neuron_a"]
            target_id = row["neuron_b"]
            count = row["count"]

            # Find synapse
            synapse = next(
                (
                    s
                    for s in self.synapses.values()
                    if s.source_id == source_id and s.target_id == target_id
                ),
                None,
            )

            if synapse:
                # Hebbian rule: strengthen connections that fire together
                delta_weight = synapse.plasticity * (count / 100.0)

                if count > 10:  # Frequent co-activation
                    # Long-term potentiation (LTP)
                    synapse.weight = min(synapse.weight + delta_weight, 1.0)
                    synapse.state = PathwayState.POTENTIATED
                    self.metrics["pathways_potentiated"] += 1
                elif count < 2:  # Rare co-activation
                    # Long-term depression (LTD)
                    synapse.weight = max(synapse.weight - delta_weight, 0.01)
                    synapse.state = PathwayState.DEPRESSED
                    self.metrics["pathways_depressed"] += 1

                # Update in database
                await self._db_execute_with_retry(
                    """
                    UPDATE brainops_synapses
                    SET weight = $2, state = $3
                    WHERE synapse_id = $1
                """,
                    synapse.id,
                    synapse.weight,
                    synapse.state.value,
                )

                # Update neuron input weights
                if target_id in self.neurons:
                    self.neurons[target_id].input_weights[source_id] = synapse.weight

        # Reset co-activation counts for next period
        await self._db_execute_with_retry(
            """
            UPDATE brainops_co_activations
            SET count = 0
            WHERE last_co_activation < NOW() - INTERVAL '1 hour'
        """
        )

        logger.info(
            f"Hebbian learning complete: {self.metrics['pathways_potentiated']} potentiated, {self.metrics['pathways_depressed']} depressed"
        )

    async def _synaptic_decay_loop(self):
        """Apply decay to unused synapses"""
        while not self._shutdown.is_set():
            try:
                # Run every hour
                await asyncio.sleep(3600)

                # Decay weights of unused synapses
                await self._db_execute_with_retry(
                    """
                    UPDATE brainops_synapses
                    SET weight = GREATEST(weight * 0.99, 0.01)
                    WHERE last_active < NOW() - INTERVAL '24 hours'
                    OR last_active IS NULL
                """
                )

                # Mark dormant synapses
                await self._db_execute_with_retry(
                    """
                    UPDATE brainops_synapses
                    SET state = 'dormant'
                    WHERE last_active < NOW() - INTERVAL '7 days'
                    AND state != 'dormant'
                """
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Synaptic decay error: {e}")
                await asyncio.sleep(3600)

    # =========================================================================
    # CLUSTER DETECTION
    # =========================================================================

    async def _cluster_detection_loop(self):
        """Detect emergent clusters of frequently co-activated neurons"""
        while not self._shutdown.is_set():
            try:
                # Run every 30 minutes
                await asyncio.sleep(1800)

                await self._detect_clusters()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cluster detection error: {e}")
                await asyncio.sleep(1800)

    async def _detect_clusters(self):
        """Detect clusters of neurons that frequently activate together"""
        # Simple clustering based on co-activation patterns
        # In production, would use proper clustering algorithms

        # Build adjacency matrix from strong synapses
        strong_connections = [
            (s.source_id, s.target_id)
            for s in self.synapses.values()
            if s.weight > self.potentiation_threshold
        ]

        # Find connected components using simple BFS
        visited = set()
        clusters_found = []

        for start_node in self.neurons.keys():
            if start_node in visited:
                continue

            # BFS to find connected neurons
            cluster = set()
            queue = [start_node]

            while queue:
                node = queue.pop(0)
                if node in visited:
                    continue

                visited.add(node)
                cluster.add(node)

                # Find strongly connected neighbors
                for source, target in strong_connections:
                    if source == node and target not in visited:
                        queue.append(target)
                    elif target == node and source not in visited:
                        queue.append(source)

            if len(cluster) >= 3:  # Minimum cluster size
                clusters_found.append(cluster)

        # Create or update clusters
        for i, neuron_ids in enumerate(clusters_found):
            cluster_id = f"cluster_{i}"

            # Determine specialization based on agent types
            specializations = []
            for nid in neuron_ids:
                if nid in self.neurons:
                    agent_id = self.neurons[nid].agent_id
                    if agent_id and self.controller:
                        agent = self.controller.agents.get(agent_id, {})
                        spec = agent.get("type", "general")
                        specializations.append(spec)

            specialization = (
                max(set(specializations), key=specializations.count)
                if specializations
                else "general"
            )

            if cluster_id not in self.clusters:
                cluster = NeuralCluster(
                    id=cluster_id,
                    name=f"Emergent Cluster {i}",
                    neuron_ids=neuron_ids,
                    specialization=specialization,
                )
                self.clusters[cluster_id] = cluster
                self.metrics["emergent_clusters"] += 1

                # Store in database
                await self._db_execute_with_retry(
                    """
                    INSERT INTO brainops_neural_clusters
                    (cluster_id, name, neuron_ids, specialization)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (cluster_id) DO UPDATE SET
                        neuron_ids = EXCLUDED.neuron_ids,
                        specialization = EXCLUDED.specialization
                """,
                    cluster_id,
                    cluster.name,
                    list(neuron_ids),
                    specialization,
                )

    # =========================================================================
    # ACTIVITY MONITORING
    # =========================================================================

    async def _activity_monitoring_loop(self):
        """Monitor overall neural activity"""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(60)

                # Calculate activity metrics
                recent_activations = [
                    a
                    for a in self.activation_history
                    if (datetime.now() - a["timestamp"]).total_seconds() < 300
                ]

                active_neurons = len(set(a["neuron_id"] for a in recent_activations))
                total_neurons = len(self.neurons)
                activity_level = (
                    active_neurons / total_neurons if total_neurons > 0 else 0
                )

                # Log if unusual activity
                if activity_level > 0.8:
                    logger.warning(f"High neural activity: {activity_level:.1%}")
                elif activity_level < 0.1 and total_neurons > 10:
                    logger.info(f"Low neural activity: {activity_level:.1%}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Activity monitoring error: {e}")
                await asyncio.sleep(60)

    # =========================================================================
    # AGENT ROUTING
    # =========================================================================

    async def route_to_agents(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> List[str]:
        """
        Route a task to appropriate agents based on neural network state.

        Args:
            task: Task to route
            context: Task context

        Returns:
            List of agent IDs to handle the task
        """
        # Activate sensory neurons based on task keywords
        task_text = json.dumps(task).lower()
        activated_agents = []

        for neuron_id, neuron in self.neurons.items():
            if neuron.agent_id:
                # Check if neuron's specialization matches task
                metadata = neuron.metadata or {}
                capabilities = metadata.get("capabilities", [])

                relevance = 0.0
                for cap in capabilities:
                    if cap.lower() in task_text:
                        relevance += 0.3

                if relevance > 0:
                    result = await self.activate_neuron(
                        neuron_id, relevance, "task_routing"
                    )
                    if result.get("fired"):
                        activated_agents.append(neuron.agent_id)

        # Also include agents from strongly connected neurons
        for synapse in self.synapses.values():
            if synapse.weight > self.potentiation_threshold:
                source_neuron = self.neurons.get(synapse.source_id)
                target_neuron = self.neurons.get(synapse.target_id)

                if source_neuron and source_neuron.agent_id in activated_agents:
                    if target_neuron and target_neuron.agent_id:
                        if target_neuron.agent_id not in activated_agents:
                            activated_agents.append(target_neuron.agent_id)

        return activated_agents[:5]  # Limit to top 5 agents

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def activate(
        self, pattern: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compatibility method used by /brainops/neural/activate route.

        Activates the network by routing a pattern/context payload through
        the existing routing + neuron activation flow.
        """
        safe_context = context or {}
        task_payload = {"pattern": pattern, "context": safe_context}
        activated_agents = await self.route_to_agents(task_payload, safe_context)

        return {
            "pattern": pattern,
            "activated_agents": activated_agents,
            "activation_count": len(activated_agents),
            "activity_level": await self.get_activity_level(),
            "timestamp": datetime.now().isoformat(),
        }

    async def get_pathways(
        self, min_strength: float = 0.5, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Return strongest neural pathways (synapses) for observability."""
        safe_limit = max(1, min(limit, 500))
        safe_min_strength = max(0.0, min(min_strength, 1.0))

        pathways: List[Dict[str, Any]] = []
        for synapse in self.synapses.values():
            if synapse.weight < safe_min_strength:
                continue
            source = self.neurons.get(synapse.source_id)
            target = self.neurons.get(synapse.target_id)
            pathways.append(
                {
                    "id": synapse.id,
                    "source_id": synapse.source_id,
                    "target_id": synapse.target_id,
                    "source_agent_id": source.agent_id if source else None,
                    "target_agent_id": target.agent_id if target else None,
                    "weight": synapse.weight,
                    "plasticity": synapse.plasticity,
                    "state": synapse.state.value if hasattr(synapse.state, "value") else str(synapse.state),
                    "co_activation_count": synapse.co_activation_count,
                    "last_active": synapse.last_active.isoformat()
                    if synapse.last_active
                    else None,
                }
            )

        pathways.sort(key=lambda p: p.get("weight", 0), reverse=True)
        return pathways[:safe_limit]

    async def get_clusters(self) -> List[Dict[str, Any]]:
        """Return emergent neural clusters."""
        clusters: List[Dict[str, Any]] = []
        for cluster in self.clusters.values():
            clusters.append(
                {
                    "id": cluster.id,
                    "name": cluster.name,
                    "specialization": cluster.specialization,
                    "size": len(cluster.neuron_ids),
                    "neuron_ids": sorted(cluster.neuron_ids),
                    "activation_pattern": cluster.activation_pattern,
                    "created_at": cluster.created_at.isoformat()
                    if cluster.created_at
                    else None,
                }
            )

        clusters.sort(key=lambda c: c.get("size", 0), reverse=True)
        return clusters

    async def get_health(self) -> Dict[str, Any]:
        """Get neural network health"""
        active_tasks = sum(1 for t in self._tasks if not t.done())

        return {
            "status": "healthy" if active_tasks == len(self._tasks) else "degraded",
            "score": active_tasks / len(self._tasks) if self._tasks else 1.0,
            "neurons": len(self.neurons),
            "synapses": len(self.synapses),
            "clusters": len(self.clusters),
            "metrics": self.metrics.copy(),
        }

    async def get_activity_level(self) -> float:
        """Get current neural activity level (0-1)"""
        recent_activations = [
            a
            for a in self.activation_history
            if (datetime.now() - a["timestamp"]).total_seconds() < 300
        ]

        active_neurons = len(set(a["neuron_id"] for a in recent_activations))
        total_neurons = len(self.neurons)

        return active_neurons / total_neurons if total_neurons > 0 else 0.0

    async def get_network_stats(self) -> Dict[str, Any]:
        """Get detailed network statistics"""
        return {
            "total_neurons": len(self.neurons),
            "total_synapses": len(self.synapses),
            "total_clusters": len(self.clusters),
            "neuron_types": {
                nt.value: sum(1 for n in self.neurons.values() if n.neuron_type == nt)
                for nt in NeuronType
            },
            "synapse_states": {
                ps.value: sum(1 for s in self.synapses.values() if s.state == ps)
                for ps in PathwayState
            },
            "avg_synapse_weight": np.mean([s.weight for s in self.synapses.values()])
            if self.synapses
            else 0,
            "metrics": self.metrics.copy(),
        }

    async def shutdown(self):
        """Shutdown the neural network"""
        self._shutdown.set()

        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("DynamicNeuralNetwork shutdown complete")


# Singleton
_neural_network: Optional[DynamicNeuralNetwork] = None


def get_neural_network() -> Optional[DynamicNeuralNetwork]:
    """Get the neural network instance"""
    return _neural_network
