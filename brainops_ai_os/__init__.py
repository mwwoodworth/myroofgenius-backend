"""
BrainOps AI OS - The Unified Artificial General Intelligence Operating System

This package contains the complete implementation of BrainOps AI OS:
- Unified Metacognitive Controller
- Continuous Awareness System
- Unified Memory Substrate
- Dynamic Neural Pathway System
- Hierarchical Goal Architecture
- Closed-Loop Learning Pipeline
- Proactive Intelligence Engine
- Reasoning Engine
- Self-Optimization System

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "BrainOps AI"

from .metacognitive_controller import MetacognitiveController, get_metacognitive_controller
from .awareness_system import AwarenessSystem, get_awareness_system
from .unified_memory import UnifiedMemorySubstrate, get_unified_memory
from .neural_dynamics import DynamicNeuralNetwork, get_neural_network
from .goal_architecture import GoalArchitecture, get_goal_architecture
from .learning_pipeline import LearningPipeline, get_learning_pipeline
from .proactive_engine import ProactiveIntelligenceEngine, get_proactive_engine
from .reasoning_engine import ReasoningEngine, get_reasoning_engine
from .self_optimization import SelfOptimizationSystem, get_self_optimization

# Global singleton instance
_brainops_controller = None


async def initialize_brainops(db_pool) -> MetacognitiveController:
    """
    Initialize the BrainOps AI OS

    This is the main entry point for starting the entire AI operating system.
    It initializes the metacognitive controller which then bootstraps all
    subsystems including:
    - Continuous Awareness System
    - Unified Memory Substrate
    - Dynamic Neural Network
    - Goal Architecture
    - Learning Pipeline
    - Proactive Intelligence Engine
    - Reasoning Engine
    - Self-Optimization System

    Args:
        db_pool: asyncpg database connection pool

    Returns:
        MetacognitiveController: The initialized controller instance
    """
    global _brainops_controller

    if _brainops_controller is not None:
        return _brainops_controller

    # Create the metacognitive controller
    controller = MetacognitiveController()

    # Initialize with database pool
    await controller.initialize(db_pool)

    # Store as singleton
    _brainops_controller = controller

    return controller


def get_brainops_controller() -> MetacognitiveController:
    """Get the BrainOps controller singleton"""
    return _brainops_controller


__all__ = [
    # Main initialization
    "initialize_brainops",
    "get_brainops_controller",
    # Metacognitive Controller
    "MetacognitiveController",
    "get_metacognitive_controller",
    # Awareness System
    "AwarenessSystem",
    "get_awareness_system",
    # Unified Memory
    "UnifiedMemorySubstrate",
    "get_unified_memory",
    # Neural Dynamics
    "DynamicNeuralNetwork",
    "get_neural_network",
    # Goal Architecture
    "GoalArchitecture",
    "get_goal_architecture",
    # Learning Pipeline
    "LearningPipeline",
    "get_learning_pipeline",
    # Proactive Engine
    "ProactiveIntelligenceEngine",
    "get_proactive_engine",
    # Reasoning Engine
    "ReasoningEngine",
    "get_reasoning_engine",
    # Self-Optimization
    "SelfOptimizationSystem",
    "get_self_optimization",
]
