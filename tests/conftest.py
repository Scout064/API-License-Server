# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

# Ensure JWT_SECRET exists for auth during tests
os.environ["JWT_SECRET"] = "testsecret123"

@pytest.fixture(scope="module")
def client():
    # Patch RateLimiter so it does nothing in tests
    with patch("app.routes.RateLimiter") as mock_limiter:
        mock_limiter.return_value.__call__ = lambda *args, **kwargs: None
        yield TestClient(app)
