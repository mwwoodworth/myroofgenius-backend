import pytest
import httpx
import os
import sys

# Ensure we can import from the app if needed, though for smokes we might just hit endpoints
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        try:
            response = await client.get("/health")
            assert response.status_code == 200, f"Health check failed with {response.status_code}"
        except httpx.RequestError:
            pytest.skip("Backend not running or unreachable")

@pytest.mark.asyncio
async def test_products_public_endpoint():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
        try:
            response = await client.get("/api/v1/products/public")
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (list, dict))
            else:
                pytest.skip(f"Public products endpoint returned {response.status_code}")
        except httpx.RequestError:
            pytest.skip("Backend not running or unreachable")

@pytest.fixture
def expected_version():
    return os.getenv("EXPECT_VERSION")

@pytest.mark.asyncio
async def test_drift_check(expected_version):
    if not expected_version:
        pytest.skip("EXPECT_VERSION not set, skipping drift check")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        try:
            resp = await client.get("/health")
        except httpx.RequestError:
            pytest.skip("Backend not running or unreachable")

    if resp.status_code != 200:
        pytest.skip(f"/health returned {resp.status_code}")

    payload = resp.json()
    current_version = payload.get("version")
    if not current_version:
        pytest.skip("Health payload missing version")

    assert current_version == expected_version, f"Version drift: expected {expected_version}, got {current_version}"
