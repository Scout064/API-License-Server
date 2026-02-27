# tests/conftest.py
import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_admin_token
from fastapi_limiter.depends import RateLimiter

# Set up test client
client = TestClient(app)

# Admin headers fixture
@pytest.fixture(scope="session")
def admin_headers():
    token = get_admin_token()
    return {"Authorization": f"Bearer {token}"}

# Ensure event loop is available for async tests
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Patch RateLimiter to avoid actual Redis calls during tests
@pytest.fixture(autouse=True)
def patch_rate_limiter(monkeypatch):
    # Replace identifier with a simple async function
    async def fake_identifier(request):
        return "test_key"

    monkeypatch.setattr(RateLimiter, "identifier", fake_identifier)
