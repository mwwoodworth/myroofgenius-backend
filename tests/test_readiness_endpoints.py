def test_ready_endpoint_fast_mode(test_client):
    response = test_client.get("/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert "database" in payload["checks"]


def test_capabilities_requires_auth(test_client, auth_headers):
    response = test_client.get("/capabilities", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "myroofgenius-backend"
    paths = {route["path"] for route in payload.get("routes", [])}
    assert "/ready" in paths


def test_diagnostics_with_admin_key(test_client, auth_headers, monkeypatch):
    monkeypatch.setenv("BRAINOPS_DIAGNOSTICS_KEY", "diag-key")
    response = test_client.get(
        "/diagnostics",
        headers={**auth_headers, "X-Admin-Key": "diag-key"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def test_diagnostics_with_diagnostics_key_header(test_client, auth_headers, monkeypatch):
    monkeypatch.setenv("BRAINOPS_DIAGNOSTICS_KEY", "diag-key")
    response = test_client.get(
        "/diagnostics",
        headers={**auth_headers, "X-Diagnostics-Key": "diag-key"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
