import os
import sys
import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

# 1. NEUTRALIZE RATE LIMITER
import fastapi_limiter
fastapi_limiter.FastAPILimiter.redis = AsyncMock()
fastapi_limiter.FastAPILimiter.init = AsyncMock()
fastapi_limiter.FastAPILimiter.identifier = AsyncMock(return_value="test-user")
fastapi_limiter.FastAPILimiter.http_callback = AsyncMock()

# Ensure app directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# CRITICAL FIX: Import models so Base.metadata knows about the 'clients' table
try:
    from app import models 
except ImportError:
    # Fallback in case your directory structure requires a direct import
    from app.models import Base as _

# 2. DATABASE SETUP (In-Memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool, 
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Tables are created here using the metadata from imported models
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# 3. AUTHENTICATION FIXTURES
# Re-adding these to fix the "fixture not found" error
def generate_test_headers(role: str):
    # Using the secret defined in your GitHub Actions environment
    secret = os.getenv("JWT_SECRET", "testsecret123")
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
    return generate_test_headers("reader")

@pytest.fixture()
def user_headers():
    return generate_test_headers("user")
