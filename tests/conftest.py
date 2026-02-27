# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Set environment variables for auth
os.environ["JWT_SECRET"] = "testsecret123"

# Patch database environment variables to bypass RuntimeError
os.environ["DB_USER"] = "test"
os.environ["DB_PASS"] = "test"
os.environ["DB_NAME"] = "test"
os.environ["DB_HOST"] = "localhost"

# Patch FastAPILimiter so it doesn't require Redis
@pytest.fixture(scope="module")
def client():
    with patch("app.routes.RateLimiter") as mock_limiter:
        mock_limiter.return_value.__call__ = lambda *args, **kwargs: None
        yield TestClient(__import__("app.main").main.app)
