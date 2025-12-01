"""
Pytest Configuration and Fixtures
Shared test setup for all BrainOps tests
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
import psycopg2
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test database configuration
TEST_DB_CONFIG = {
    "host": "aws-0-us-east-2.pooler.supabase.com",
    "database": "postgres",
    "user": "postgres.yomagoqdmxszqtdwuhab",
    "password": "Brain0ps2O2S",
    "port": 6543
}

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def db_connection():
    """Database connection for tests"""
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    yield conn
    conn.close()

@pytest.fixture
def db_cursor(db_connection):
    """Database cursor with transaction rollback"""
    cursor = db_connection.cursor()
    yield cursor
    # Connection may already be closed or may be a lightweight stub without a
    # `.closed` attribute (as in some unit tests). Guard accordingly so teardown
    # never raises and real connections still get rolled back.
    try:
        closed_flag = getattr(db_connection, "closed", 0)
        if not closed_flag:
            db_connection.rollback()  # Rollback after each test
    except Exception:
        # Best-effort rollback only; ignore teardown errors.
        pass
    cursor.close()

@pytest.fixture
async def async_db_pool():
    """Async database pool"""
    import asyncpg
    pool = await asyncpg.create_pool(
        host=TEST_DB_CONFIG["host"],
        database=TEST_DB_CONFIG["database"],
        user=TEST_DB_CONFIG["user"],
        password=TEST_DB_CONFIG["password"],
        port=TEST_DB_CONFIG["port"],
        min_size=2,
        max_size=10
    )
    yield pool
    await pool.close()

@pytest.fixture
def test_client():
    """FastAPI test client"""
    try:
        from main import app
        client = TestClient(app)
        yield client
    except ImportError:
        pytest.skip("FastAPI app not available")

@pytest.fixture
def auth_headers():
    """Authentication headers for tests"""
    # TODO: Generate test JWT token
    return {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json"
    }

@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "email": "test@brainops.com",
        "password": "TestPassword123!",
        "name": "Test User"
    }

@pytest.fixture
def test_customer_data():
    """Test customer data"""
    return {
        "name": "Test Customer",
        "email": "customer@test.com",
        "phone": "555-0100",
        "address": "123 Test St",
        "city": "Denver",
        "state": "CO",
        "zip": "80202"
    }

@pytest.fixture
def test_job_data():
    """Test job data"""
    return {
        "customer_id": "test-customer-id",
        "job_type": "Roof Repair",
        "status": "scheduled",
        "scheduled_date": "2025-10-20",
        "estimated_cost": 5000.00
    }

@pytest.fixture(autouse=True)
def reset_test_data(db_cursor):
    """Reset test data before each test"""
    # Clean up test data
    tables = [
        'test_data',
        'test_sessions'
    ]
    for table in tables:
        try:
            db_cursor.execute(f"DELETE FROM {table} WHERE email LIKE '%@test.com'")
        except:
            pass  # Table may not exist
    yield

@pytest.fixture
def mock_ai_response():
    """Mock AI agent response"""
    return {
        "success": True,
        "result": {
            "analysis": "Test analysis",
            "recommendations": ["Test recommendation 1", "Test recommendation 2"],
            "confidence": 0.95
        },
        "agent": "test_agent",
        "duration_ms": 150
    }

@pytest.fixture
def mock_openai_embedding():
    """Mock OpenAI embedding"""
    import random
    return [random.random() for _ in range(1536)]

# Performance timing fixture
@pytest.fixture
def timer():
    """Timer for performance tests"""
    import time
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()

# Markers for CI/CD
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "ci: Mark test to run in CI/CD pipeline"
    )
    config.addinivalue_line(
        "markers", "local: Mark test for local development only"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Skip slow tests in CI if --ci flag is passed
    if config.getoption("--ci", default=False):
        skip_slow = pytest.mark.skip(reason="Slow test skipped in CI")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--ci",
        action="store_true",
        default=False,
        help="Run in CI mode (skip slow tests)"
    )
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests"
    )
    parser.addoption(
        "--e2e",
        action="store_true",
        default=False,
        help="Run end-to-end tests"
    )
