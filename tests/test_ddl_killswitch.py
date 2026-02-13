"""
V7 P0-A: Runtime DDL Kill-Switch — Deterministic Tests

Verifies that assert_no_runtime_ddl() blocks DDL in production/staging
and allows DML (INSERT/UPDATE/DELETE/SELECT) to pass through.
"""
import os
import pytest
from unittest.mock import patch


def _fresh_import():
    """Import the module with fresh env state (module caches env at import time)."""
    import importlib
    import brainops_ai_os._resilience as mod

    importlib.reload(mod)
    return mod


class TestDDLDetection:
    """Test the _is_ddl() regex."""

    def test_create_table(self):
        from brainops_ai_os._resilience import _is_ddl

        assert _is_ddl("CREATE TABLE IF NOT EXISTS foo (id int)")

    def test_alter_table(self):
        from brainops_ai_os._resilience import _is_ddl

        assert _is_ddl("ALTER TABLE foo ADD COLUMN bar TEXT")

    def test_drop_table(self):
        from brainops_ai_os._resilience import _is_ddl

        assert _is_ddl("DROP TABLE foo")

    def test_grant(self):
        from brainops_ai_os._resilience import _is_ddl

        assert _is_ddl("GRANT SELECT ON foo TO bar")

    def test_revoke(self):
        from brainops_ai_os._resilience import _is_ddl

        assert _is_ddl("REVOKE ALL ON foo FROM bar")

    def test_truncate(self):
        from brainops_ai_os._resilience import _is_ddl

        assert _is_ddl("TRUNCATE TABLE foo")

    def test_create_with_comments(self):
        from brainops_ai_os._resilience import _is_ddl

        assert _is_ddl("-- comment\nCREATE TABLE foo (id int)")

    def test_insert_not_ddl(self):
        from brainops_ai_os._resilience import _is_ddl

        assert not _is_ddl("INSERT INTO foo VALUES (1)")

    def test_update_not_ddl(self):
        from brainops_ai_os._resilience import _is_ddl

        assert not _is_ddl("UPDATE foo SET bar = 1")

    def test_delete_not_ddl(self):
        from brainops_ai_os._resilience import _is_ddl

        assert not _is_ddl("DELETE FROM foo WHERE id = 1")

    def test_select_not_ddl(self):
        from brainops_ai_os._resilience import _is_ddl

        assert not _is_ddl("SELECT * FROM foo")

    def test_create_extension(self):
        from brainops_ai_os._resilience import _is_ddl

        assert _is_ddl("CREATE EXTENSION IF NOT EXISTS vector")

    def test_whitespace_prefix(self):
        from brainops_ai_os._resilience import _is_ddl

        assert _is_ddl("   \n  CREATE TABLE foo (id int)")


class TestKillSwitchProduction:
    """Test that DDL is ALWAYS blocked in production."""

    def test_production_blocks_ddl(self):
        with patch.dict(
            os.environ, {"ENVIRONMENT": "production", "ENABLE_RUNTIME_DDL": "1"}
        ):
            mod = _fresh_import()
            with pytest.raises(RuntimeError, match="BLOCKED_RUNTIME_DDL"):
                mod.assert_no_runtime_ddl("CREATE TABLE foo (id int)")

    def test_staging_blocks_ddl(self):
        with patch.dict(
            os.environ, {"ENVIRONMENT": "staging", "ENABLE_RUNTIME_DDL": "1"}
        ):
            mod = _fresh_import()
            with pytest.raises(RuntimeError, match="BLOCKED_RUNTIME_DDL"):
                mod.assert_no_runtime_ddl("CREATE TABLE foo (id int)")

    def test_production_allows_dml(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            mod = _fresh_import()
            mod.assert_no_runtime_ddl("INSERT INTO foo VALUES (1)")  # should not raise
            mod.assert_no_runtime_ddl("UPDATE foo SET bar = 1")
            mod.assert_no_runtime_ddl("SELECT * FROM foo")


class TestKillSwitchDev:
    """Test DDL gating in non-production environments."""

    def test_dev_blocks_ddl_by_default(self):
        with patch.dict(
            os.environ,
            {"ENVIRONMENT": "development", "ENABLE_RUNTIME_DDL": ""},
            clear=False,
        ):
            mod = _fresh_import()
            with pytest.raises(RuntimeError, match="BLOCKED_RUNTIME_DDL"):
                mod.assert_no_runtime_ddl("CREATE TABLE foo (id int)")

    def test_dev_allows_ddl_with_opt_in(self):
        with patch.dict(
            os.environ, {"ENVIRONMENT": "development", "ENABLE_RUNTIME_DDL": "1"}
        ):
            mod = _fresh_import()
            mod.assert_no_runtime_ddl("CREATE TABLE foo (id int)")  # should not raise

    def test_no_env_blocks_ddl_by_default(self):
        env = os.environ.copy()
        env.pop("ENVIRONMENT", None)
        env.pop("ENABLE_RUNTIME_DDL", None)
        with patch.dict(os.environ, env, clear=True):
            mod = _fresh_import()
            with pytest.raises(RuntimeError, match="BLOCKED_RUNTIME_DDL"):
                mod.assert_no_runtime_ddl("DROP TABLE foo")
