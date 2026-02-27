import os
import sys
import pytest
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure the app directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import Base, get_db

# 1. Database Setup: Use an in-memory SQLite for isolated testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Creates tables for each test and provides a session."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

# 2. Test Client with Dependency Injection
@pytest.fixture(scope="function")
def client(db_session):
    """Overrides the get_db dependency to use the test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# 3. Mock Rate Limiter (Prevents Redis connection errors in CI)
@pytest.fixture(autouse=True, scope="session")
def patch_fastapi_limiter():
    from unittest.mock import AsyncMock, patch
    with patch("fastapi_limiter.FastAPILimiter.init", new=AsyncMock()), \
         patch("fastapi_limiter.FastAPILimiter.redis", new=AsyncMock()), \
         patch("fastapi_limiter.FastAPILimiter.identifier", new=AsyncMock(return_value="test")):
        yield

# 4. Authentication Headers
def generate_test_headers(role: str):
    secret = os.getenv("JWT_SECRET", "fallback_test_secret")
    payload = {
        "user_id": 99,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture()
def admin_headers():
    return generate_test_headers("admin")

@pytest.fixture()
def reader_headers():
    """Fixes the 403 error for the validation endpoint."""
    return generate_test_headers("reader")

@pytest.fixture()
def user_headers():
    return generate_test_headers("user")
