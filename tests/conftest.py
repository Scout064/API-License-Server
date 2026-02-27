# File: tests/conftest.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- Set test environment variables ---
os.environ["DB_USER"] = "testuser"
os.environ["DB_PASS"] = "testpass"
os.environ["DB_NAME"] = "testdb"
os.environ["DB_HOST"] = "localhost"
os.environ["JWT_SECRET"] = "testsecret123"

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.auth import create_token
from sqlalchemy.orm import Session

# ---------------------------
# Patch FastAPILimiter correctly
# ---------------------------
@pytest.fixture(autouse=True, scope="session")
def patch_fastapi_limiter():
    """Mocks FastAPILimiter to prevent Redis calls during tests."""
    mock_redis = AsyncMock()
    mock_redis.evalsha = AsyncMock(return_value=1)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)

    with patch("fastapi_limiter.FastAPILimiter.init", new=AsyncMock()), \
         patch("fastapi_limiter.FastAPILimiter.redis", new=mock_redis), \
         patch("fastapi_limiter.FastAPILimiter.identifier", new=AsyncMock(return_value="test_key")), \
         patch("fastapi_limiter.FastAPILimiter.http_callback", new=AsyncMock(return_value=None)):
        yield

# ---------------------------
# Mock DB session for tests
# ---------------------------
@pytest.fixture()
def db_session():
    session = AsyncMock(spec=Session)
    yield session

# Override the app dependency
@pytest.fixture(autouse=True)
def override_get_db(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield app.dependency_overrides.clear()

# ---------------------------
# Test client
# ---------------------------
@pytest.fixture()
def client():
    return TestClient(app)

# ---------------------------
# JWT token fixtures
# ---------------------------
@pytest.fixture()
def admin_token():
    """JWT token for admin user"""
    return create_token(user_id=1, role="admin")

@pytest.fixture()
def user_token():
    """JWT token for normal user"""
    return create_token(user_id=2, role="user")

# ---------------------------
# Headers fixtures
# ---------------------------
@pytest.fixture()
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture()
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}
