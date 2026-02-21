"""
Phase 02: Alert Signal Quality — Regression Tests

Tests:
1. Sustained breach logic (_check_sustained_breach)
2. Feedback loop prevention (thought type = "alert_raised", not "alert")
3. handle_alert reads "alert_type" field before "type"
4. Threshold configurability via ALERT_THRESHOLDS
5. Upsert SQL uses ON CONFLICT clause
6. In-memory dedup prevents duplicate _generate_alert calls
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime
from collections import deque

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestSustainedBreachLogic:
    """Test _check_sustained_breach rolling window"""

    def _make_system(self):
        """Create a minimal AwarenessSystem for testing"""
        from brainops_ai_os.awareness_system import AwarenessSystem

        controller = MagicMock()
        system = AwarenessSystem(controller)
        return system

    def test_single_breach_does_not_trigger(self):
        system = self._make_system()
        # Single breach below window size (default 3)
        result = system._check_sustained_breach("cpu", 96.0, 95.0)
        assert result is False, "Single breach should not trigger alert"

    def test_two_breaches_does_not_trigger(self):
        system = self._make_system()
        system._check_sustained_breach("cpu", 96.0, 95.0)
        result = system._check_sustained_breach("cpu", 97.0, 95.0)
        assert result is False, "Two breaches should not trigger (window=3)"

    def test_three_consecutive_breaches_triggers(self):
        system = self._make_system()
        system._check_sustained_breach("cpu", 96.0, 95.0)
        system._check_sustained_breach("cpu", 97.0, 95.0)
        result = system._check_sustained_breach("cpu", 98.0, 95.0)
        assert result is True, "Three consecutive breaches should trigger"

    def test_breach_cleared_by_normal_reading(self):
        system = self._make_system()
        system._check_sustained_breach("cpu", 96.0, 95.0)
        system._check_sustained_breach("cpu", 97.0, 95.0)
        # Normal reading clears the window
        result = system._check_sustained_breach("cpu", 80.0, 95.0)
        assert result is False, "Normal reading should clear breach state"

    def test_breach_after_clear_requires_full_window(self):
        system = self._make_system()
        # Build up breach
        system._check_sustained_breach("cpu", 96.0, 95.0)
        system._check_sustained_breach("cpu", 97.0, 95.0)
        # Clear
        system._check_sustained_breach("cpu", 80.0, 95.0)
        # New breaches need full window again
        system._check_sustained_breach("cpu", 96.0, 95.0)
        result = system._check_sustained_breach("cpu", 97.0, 95.0)
        assert result is False, "After clear, need full window of breaches again"

    def test_independent_metrics(self):
        system = self._make_system()
        # Build up CPU breaches
        system._check_sustained_breach("cpu", 96.0, 95.0)
        system._check_sustained_breach("cpu", 97.0, 95.0)
        system._check_sustained_breach("cpu", 98.0, 95.0)
        # Memory is independent — should not trigger
        result = system._check_sustained_breach("memory", 96.0, 95.0)
        assert result is False, "Different metrics should have independent windows"

    def test_window_size_respects_config(self):
        system = self._make_system()
        with patch("brainops_ai_os.awareness_system.BREACH_WINDOW_SIZE", 5):
            for i in range(4):
                system._check_sustained_breach("cpu", 96.0 + i, 95.0)
            result = system._check_sustained_breach("cpu", 99.0, 95.0)
            assert result is True, "Window size 5 should trigger after 5 breaches"

    def test_exactly_at_threshold_does_not_breach(self):
        system = self._make_system()
        for _ in range(5):
            result = system._check_sustained_breach("cpu", 95.0, 95.0)
        assert result is False, "Value at threshold (not above) should not breach"


class TestFeedbackLoopPrevention:
    """Test that _generate_alert uses 'alert_raised' thought type"""

    @pytest.mark.asyncio
    async def test_thought_type_is_alert_raised(self):
        """The controller notification must use 'alert_raised' to avoid re-routing"""
        from brainops_ai_os.awareness_system import AwarenessSystem, AlertSeverity

        controller = MagicMock()
        controller._record_thought = AsyncMock()
        system = AwarenessSystem(controller)
        system.db_pool = MagicMock()

        # Mock DB execute
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        system.db_pool.acquire = MagicMock(return_value=AsyncMock())
        system._db_execute_with_retry = AsyncMock()

        await system._generate_alert(
            AlertSeverity.WARNING,
            "slow_database",
            "Test slow query",
            {"query_time_ms": 3000},
        )

        # Verify controller was notified
        assert controller._record_thought.called, "Controller should be notified"
        thought_content = controller._record_thought.call_args[0][0]
        assert (
            thought_content["type"] == "alert_raised"
        ), f"Thought type must be 'alert_raised', got '{thought_content['type']}'"
        assert thought_content["alert_type"] == "slow_database"

    @pytest.mark.asyncio
    async def test_info_severity_does_not_notify_controller(self):
        """INFO alerts should not notify the controller"""
        from brainops_ai_os.awareness_system import AwarenessSystem, AlertSeverity

        controller = MagicMock()
        controller._record_thought = AsyncMock()
        system = AwarenessSystem(controller)
        system._db_execute_with_retry = AsyncMock()

        await system._generate_alert(
            AlertSeverity.INFO,
            "business_anomaly",
            "Test anomaly",
            {},
        )

        assert (
            not controller._record_thought.called
        ), "INFO alerts should not notify controller"


class TestHandleAlertFieldReading:
    """Test that handle_alert reads alert_type before type"""

    @pytest.mark.asyncio
    async def test_reads_alert_type_field(self):
        """handle_alert should use 'alert_type' field if present"""
        from brainops_ai_os.awareness_system import AwarenessSystem, AlertSeverity

        controller = MagicMock()
        system = AwarenessSystem(controller)
        system._db_execute_with_retry = AsyncMock()
        system._generate_alert = AsyncMock()

        await system.handle_alert(
            {
                "type": "alert",  # thought classification (wrong for alert_type)
                "alert_type": "subsystem_unhealthy_awareness",  # correct value
                "severity": "warning",
                "message": "Test",
                "details": {},
            }
        )

        # _generate_alert should receive the correct alert_type
        call_args = system._generate_alert.call_args
        actual_type = call_args[0][1]  # second positional arg
        assert (
            actual_type == "subsystem_unhealthy_awareness"
        ), f"handle_alert should read 'alert_type' field, got '{actual_type}'"

    @pytest.mark.asyncio
    async def test_falls_back_to_type_field(self):
        """handle_alert should fall back to 'type' if 'alert_type' missing"""
        from brainops_ai_os.awareness_system import AwarenessSystem

        controller = MagicMock()
        system = AwarenessSystem(controller)
        system._db_execute_with_retry = AsyncMock()
        system._generate_alert = AsyncMock()

        await system.handle_alert(
            {
                "type": "service_down",
                "severity": "warning",
                "message": "Test",
                "details": {},
            }
        )

        call_args = system._generate_alert.call_args
        actual_type = call_args[0][1]
        assert (
            actual_type == "service_down"
        ), f"Should fall back to 'type' field, got '{actual_type}'"

    @pytest.mark.asyncio
    async def test_falls_back_to_external(self):
        """handle_alert defaults to 'external' if no type fields present"""
        from brainops_ai_os.awareness_system import AwarenessSystem

        controller = MagicMock()
        system = AwarenessSystem(controller)
        system._db_execute_with_retry = AsyncMock()
        system._generate_alert = AsyncMock()

        await system.handle_alert(
            {
                "severity": "info",
                "message": "Test",
            }
        )

        call_args = system._generate_alert.call_args
        actual_type = call_args[0][1]
        assert actual_type == "external"


class TestUpsertSQL:
    """Test that the INSERT uses ON CONFLICT for dedup"""

    @pytest.mark.asyncio
    async def test_insert_contains_on_conflict(self):
        """The DB INSERT must include ON CONFLICT clause"""
        from brainops_ai_os.awareness_system import AwarenessSystem, AlertSeverity

        controller = MagicMock()
        controller._record_thought = AsyncMock()
        system = AwarenessSystem(controller)
        system._db_execute_with_retry = AsyncMock()

        await system._generate_alert(
            AlertSeverity.WARNING,
            "test_alert",
            "Test message",
            {"key": "value"},
        )

        call_args = system._db_execute_with_retry.call_args
        sql = call_args[0][0]
        assert "ON CONFLICT" in sql, "INSERT must use ON CONFLICT for dedup"
        assert (
            "alert_type" in sql and "severity" in sql
        ), "ON CONFLICT must reference alert_type and severity"
        assert "last_seen_at" in sql, "Upsert must update last_seen_at"


class TestInMemoryDedup:
    """Test that in-memory dict prevents duplicate _generate_alert calls"""

    @pytest.mark.asyncio
    async def test_duplicate_alert_is_suppressed(self):
        """Second call with same type+severity should be suppressed"""
        from brainops_ai_os.awareness_system import AwarenessSystem, AlertSeverity

        controller = MagicMock()
        controller._record_thought = AsyncMock()
        system = AwarenessSystem(controller)
        system._db_execute_with_retry = AsyncMock()

        # First call
        await system._generate_alert(
            AlertSeverity.WARNING, "high_cpu", "CPU at 96%", {}
        )
        assert system._db_execute_with_retry.call_count == 1

        # Second call — should be suppressed by in-memory dedup
        await system._generate_alert(
            AlertSeverity.WARNING, "high_cpu", "CPU at 97%", {}
        )
        assert (
            system._db_execute_with_retry.call_count == 1
        ), "Duplicate alert should be suppressed by in-memory dedup"

    @pytest.mark.asyncio
    async def test_different_types_are_not_suppressed(self):
        """Different alert types should not suppress each other"""
        from brainops_ai_os.awareness_system import AwarenessSystem, AlertSeverity

        controller = MagicMock()
        controller._record_thought = AsyncMock()
        system = AwarenessSystem(controller)
        system._db_execute_with_retry = AsyncMock()

        await system._generate_alert(
            AlertSeverity.WARNING, "high_cpu", "CPU at 96%", {}
        )
        await system._generate_alert(
            AlertSeverity.WARNING, "slow_database", "DB slow", {}
        )
        assert system._db_execute_with_retry.call_count == 2


class TestThresholdConfig:
    """Test that thresholds are configurable"""

    def test_default_thresholds(self):
        from brainops_ai_os.awareness_system import ALERT_THRESHOLDS

        assert (
            ALERT_THRESHOLDS["cpu_percent"] == 95.0
        ), "Default CPU threshold should be 95%"
        assert (
            ALERT_THRESHOLDS["db_query_ms"] == 2000.0
        ), "Default DB threshold should be 2000ms"

    def test_env_override(self):
        """Thresholds should be overridable via env vars"""
        import importlib
        import os

        os.environ["ALERT_THRESHOLD_CPU"] = "80"
        try:
            import brainops_ai_os.awareness_system as module

            importlib.reload(module)
            assert module.ALERT_THRESHOLDS["cpu_percent"] == 80.0
        finally:
            del os.environ["ALERT_THRESHOLD_CPU"]
            importlib.reload(module)
