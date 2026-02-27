import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

# ---------------------------
# Mock DB for tests
# ---------------------------
@pytest.fixture(autouse=True, scope="session")
def patch_get_db():
    # Patch get_db before importing routes
    mock_db = AsyncMock()
    with patch("app.routes.get_db", return_value=mock_db), \
         patch("app.database.get_db", return_value=mock_db):
        yield

# ---------------------------
# Patch FastAPILimiter
# ---------------------------
@pytest.fixture(autouse=True, scope="session")
def patch_fastapi_limiter():
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
# Test client
# ---------------------------
@pytest.fixture()
def client():
    return TestClient(app)

# ---------------------------
# JWT tokens
# ---------------------------
from app.auth import create_token

@pytest.fixture()
def admin_token():
    return create_token(user_id=1, role="admin", secret=JWT_SECRET)

@pytest.fixture()
def user_token():
    return create_token(user_id=2, role="user", secret=JWT_SECRET)

@pytest.fixture()
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture()
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}
