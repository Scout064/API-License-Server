import os
import pytest
from unittest.mock import AsyncMock, patch  # <-- import AsyncMock

# --- Set test environment variables ---
os.environ["DB_USER"] = "testuser"
os.environ["DB_PASS"] = "testpass"
os.environ["DB_NAME"] = "testdb"
os.environ["DB_HOST"] = "localhost"
os.environ["JWT_SECRET"] = "testsecret123"

# --- Patch FastAPILimiter.init to prevent Redis errors ---
@pytest.fixture(autouse=True, scope="session")
def patch_fastapi_limiter_init():
    with patch("fastapi_limiter.FastAPILimiter.init", new=AsyncMock()):
        yield

# --- Patch DB session so tests don't require a real database ---
@pytest.fixture(autouse=True)
def patch_db_session():
    with patch("app.database.get_db") as mock_db:
        mock_db.return_value = iter([])  # empty generator for testing
        yield mock_db
