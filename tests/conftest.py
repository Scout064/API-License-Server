# tests/conftest.py
import os
os.environ["DB_USER"] = "testuser"
os.environ["DB_PASS"] = "testpass"
os.environ["DB_NAME"] = "testdb"
os.environ["DB_HOST"] = "localhost"
os.environ["JWT_SECRET"] = "testsecret123"
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

# Patch FastAPILimiter so it doesn't require Redis
@pytest.fixture(scope="module")
def client():
    with patch("app.routes.RateLimiter") as mock_limiter:
        mock_limiter.return_value.__call__ = lambda *args, **kwargs: None
        yield TestClient(__import__("app.main").main.app)

# Mock admin token headers for tests
@pytest.fixture(scope="session")
def admin_headers():
    return {"Authorization": "Bearer test_admin_token"}

# Patch the slowapi Limiter to a no-op during tests
@pytest.fixture(autouse=True, scope="session")
def disable_rate_limiter():
    with patch("app.routes.limiter") as mock_limiter:
        mock_limiter.limit = lambda *args, **kwargs: (lambda f: f)  # Decorator no-op
        yield

# Provide a test client
@pytest.fixture(scope="session")
def client():
    return TestClient(app)
