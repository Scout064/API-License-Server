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

# =========================================================================
# CRITICAL FIX: You MUST import your models here.
# If your models are in app/models.py, import them like this:
# from app import models 
# or 
# from app.models import Client, License  # (Use your actual model names)
# =========================================================================
from app import models  # Ensure this line points to where your 'Client' model is

# 2. DATABASE SETUP (In-Memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool, # Required for in-memory SQLite to persist between connections
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Now that 'models' are imported, this will successfully create the 'clients' table
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

# (Keep your existing admin_headers, reader_headers, etc. fixtures here)
