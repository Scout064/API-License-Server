# tests/conftest.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import os
# --- Set test environment variables ---
os.environ["DB_USER"] = "testuser"
os.environ["DB_PASS"] = "testpass"
os.environ["DB_NAME"] = "testdb"
os.environ["DB_HOST"] = "localhost"
os.environ["JWT_SECRET"] = "testsecret123"
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_db
from sqlalchemy.orm import Session

# ---------------------------
# Patch FastAPILimiter globally
# ---------------------------
@pytest.fixture(autouse=True, scope="session")
def patch_fastapi_limiter():
    """
    Fully mocks FastAPILimiter to prevent Redis calls.
    """
    with patch("fastapi_limiter.FastAPILimiter.init", new=AsyncMock()), \
         patch("fastapi_limiter.FastAPILimiter.redis", new=True), \
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
    yield
    app.dependency_overrides.clear()

# ---------------------------
# Test client
# ---------------------------
@pytest.fixture()
def client():
    return TestClient(app)

@pytest.fixture()
def admin_headers():
    return {"Authorization": "Bearer test_admin_token"}
