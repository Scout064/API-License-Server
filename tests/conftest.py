import os
import pytest
from unittest.mock import AsyncMock, patch  # <-- import AsyncMock

# --- Set test environment variables ---
os.environ["DB_USER"] = "testuser"
os.environ["DB_PASS"] = "testpass"
os.environ["DB_NAME"] = "testdb"
os.environ["DB_HOST"] = "localhost"
os.environ["JWT_SECRET"] = "testsecret123"

# Patch FastAPILimiter before app startup
@pytest.fixture(autouse=True, scope="session")
def patch_fastapi_limiter():
    # Patch the init method so it doesn't require Redis
    with patch("fastapi_limiter.FastAPILimiter.init", new=AsyncMock()):
        # Also patch the redis attribute so RateLimiter sees it as initialized
        with patch("fastapi_limiter.FastAPILimiter.redis", new=True):
            yield
