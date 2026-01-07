import importlib.util
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
SERVER_FILES = [
    ROOT / "myroofgenius-backend" / "mcp-servers" / "erp-mcp" / "server.py",
    ROOT / "myroofgenius-backend" / "mcp-servers" / "database-mcp" / "server.py",
    ROOT / "myroofgenius-backend" / "mcp-servers" / "crm-mcp" / "server.py",
    ROOT / "myroofgenius-backend" / "mcp-servers" / "ai-orchestrator-mcp" / "server.py",
    ROOT / "myroofgenius-backend" / "mcp-servers" / "monitoring-mcp" / "server.py",
    ROOT / "myroofgenius-backend" / "mcp-servers" / "automation-mcp" / "server.py",
]


def load_app(path: Path):
    module_name = f"mcp_stub_{path.parent.name}_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.app


@pytest.mark.parametrize("server_path", SERVER_FILES)
def test_stub_disabled_by_default(server_path, monkeypatch):
    monkeypatch.delenv("ALLOW_MCP_STUBS", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("ENV", raising=False)

    app = load_app(server_path)
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 503


@pytest.mark.parametrize("server_path", SERVER_FILES)
def test_stub_enabled_in_dev(server_path, monkeypatch):
    monkeypatch.setenv("ALLOW_MCP_STUBS", "true")
    monkeypatch.setenv("ENVIRONMENT", "development")

    app = load_app(server_path)
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    payload = health.json()
    assert payload.get("stubbed") is True
    assert payload.get("ready") is False

    execute = client.post("/execute", json={"action": "ping", "params": {"foo": "bar"}})
    assert execute.status_code == 200
    assert execute.json().get("status") == "stubbed"


@pytest.mark.parametrize("server_path", SERVER_FILES)
def test_stub_forced_off_in_production(server_path, monkeypatch):
    monkeypatch.setenv("ALLOW_MCP_STUBS", "true")
    monkeypatch.setenv("ENVIRONMENT", "production")

    app = load_app(server_path)
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 503
