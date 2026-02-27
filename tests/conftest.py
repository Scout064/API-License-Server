import os
import sys
import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

# 1. NEUTRALIZE RATE LIMITER IMMEDIATELY
import fastapi_limiter
fastapi_limiter.FastAPILimiter.redis = AsyncMock()
fastapi_limiter.FastAPILimiter.init = AsyncMock()

# FIX: Prevents TypeError: 'NoneType' object is not callable
fastapi_limiter.FastAPILimiter.identifier = AsyncMock(return_value="test-user")
fastapi_limiter.FastAPILimiter.http_callback = AsyncMock()

# Ensure the app directory is in the path for GitHub Actions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Now safe to import app components
from app.main import app
from app.database import Base, get_db

# FIX: SQL Table missing error
# IMPORTANT: You must import your models here so they register with Base.metadata.
# If your models are in app/models.py, uncomment the line below:
# from app import models 

# 2. DEBUGGING: CONFIRM ROUTES ARE LOADED
@pytest.fixture(scope="session", autouse=True)
def check_routes():
    print("\n--- Registered Routes ---")
    for route in app.routes:
        path = getattr(route, 'path', 'No Path Found')
        print(f"Path: {path}")
    print("------------------------\n")

# 3. DATABASE SETUP (In-Memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool, # Maintains a single connection for the in-memory DB
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # This creates the tables based on everything registered in Base.metadata
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Wipes the DB after each test for isolation
        Base.metadata.drop_all(bind=engine)

# 4. TEST CLIENT FIXTURE
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

# 5. AUTHENTICATION HELPERS
def generate_test_headers(role: str):
    secret = os.getenv("JWT_SECRET", "test_jwt_secret")
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
