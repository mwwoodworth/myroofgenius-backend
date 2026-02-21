"""Regression tests for alert duplication fix.

Verifies:
1. Metacognitive controller does NOT route alert thoughts back to awareness system.
2. handle_alert() correctly extracts alert_type from thought content.
3. slow_database threshold is 3000ms (not 1000ms).
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class TestMetacognitiveAlertRouting:
    """Verify alert thoughts are acknowledged, not re-routed."""

    @pytest.mark.asyncio
    async def test_alert_thought_acknowledged_not_routed(self):
        """When a thought has type='alert', controller should NOT call handle_alert()."""
        from brainops_ai_os.metacognitive_controller import (
            MetacognitiveController,
        )

        controller = MetacognitiveController.__new__(MetacognitiveController)
        controller.awareness_system = MagicMock()
        controller.awareness_system.handle_alert = AsyncMock()
        controller.unified_memory = MagicMock()
        controller.goal_architecture = MagicMock()
        controller.learning_pipeline = MagicMock()
        controller.proactive_engine = MagicMock()
        controller.reasoning_engine = MagicMock()
        controller.self_optimization = MagicMock()

        # Create a thought with type="alert"
        thought = MagicMock()
        thought.content = {
            "type": "alert",
            "alert_type": "slow_database",
            "severity": "warning",
            "message": "Database query took 4500ms",
        }

        result = await controller._process_single_thought(thought)

        # Should acknowledge, NOT route to awareness_system
        assert result["status"] == "acknowledged"
        controller.awareness_system.handle_alert.assert_not_called()

    @pytest.mark.asyncio
    async def test_warning_thought_acknowledged_not_routed(self):
        """Warning thoughts should also be acknowledged, not re-routed."""
        from brainops_ai_os.metacognitive_controller import (
            MetacognitiveController,
        )

        controller = MetacognitiveController.__new__(MetacognitiveController)
        controller.awareness_system = MagicMock()
        controller.awareness_system.handle_alert = AsyncMock()
        controller.unified_memory = MagicMock()
        controller.goal_architecture = MagicMock()
        controller.learning_pipeline = MagicMock()
        controller.proactive_engine = MagicMock()
        controller.reasoning_engine = MagicMock()
        controller.self_optimization = MagicMock()

        thought = MagicMock()
        thought.content = {"type": "warning", "message": "test warning"}

        result = await controller._process_single_thought(thought)

        assert result["status"] == "acknowledged"
        controller.awareness_system.handle_alert.assert_not_called()


class TestHandleAlertKeyExtraction:
    """Verify handle_alert() reads alert_type correctly."""

    @pytest.mark.asyncio
    async def test_alert_type_key_preferred_over_type(self):
        """handle_alert() should prefer 'alert_type' over 'type' for the alert category."""
        from brainops_ai_os.awareness_system import AwarenessSystem

        system = AwarenessSystem.__new__(AwarenessSystem)
        system._generate_alert = AsyncMock()

        # Simulate thought content with both keys
        alert_data = {
            "type": "alert",
            "alert_type": "slow_database",
            "severity": "warning",
            "message": "Database query took 4500ms",
            "details": {},
        }

        await system.handle_alert(alert_data)

        # _generate_alert should be called with "slow_database", not "alert"
        call_args = system._generate_alert.call_args
        assert call_args[0][1] == "slow_database"

    @pytest.mark.asyncio
    async def test_falls_back_to_type_when_no_alert_type(self):
        """When alert_type is missing, falls back to type key."""
        from brainops_ai_os.awareness_system import AwarenessSystem

        system = AwarenessSystem.__new__(AwarenessSystem)
        system._generate_alert = AsyncMock()

        alert_data = {
            "type": "high_cpu",
            "severity": "warning",
            "message": "CPU at 95%",
            "details": {},
        }

        await system.handle_alert(alert_data)

        call_args = system._generate_alert.call_args
        assert call_args[0][1] == "high_cpu"


class TestSlowDatabaseThreshold:
    """Verify slow_database threshold is reasonable."""

    def test_threshold_is_3000ms(self):
        """Slow database alert should trigger at 3000ms, not 1000ms."""
        import inspect

        from brainops_ai_os.awareness_system import AwarenessSystem

        source = inspect.getsource(AwarenessSystem._database_sensor)
        # Should contain 3000 threshold, not 1000
        assert "query_time > 3000" in source
        assert "query_time > 1000" not in source
