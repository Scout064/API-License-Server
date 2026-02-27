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

# --- Disable rate limiting ---
@pytest.fixture(autouse=True, scope="session")
def disable_rate_limiter():
    with patch("fastapi_limiter.FastAPILimiter.init") as mock_init:
        yield mock_init

# --- Optionally: disable DB session for unit tests ---
@pytest.fixture(autouse=True)
def patch_db_session():
    with patch("app.database.get_db") as mock_db:
        mock_db.return_value = iter([])  # empty generator for testing
        yield mock_db
