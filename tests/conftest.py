import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
import jwt

# Add the app directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import Base, get_db
from app.auth import create_token

# 1. Setup an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Database fixture to create/drop tables for each test
@pytest.fixture(scope="function")
def db_session():
    # Create the tables (fixes the "no such table" error)
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)

# 3. Client fixture that overrides the dependency
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

# 4. Mocking the Rate Limiter (fixes Redis connection issues in CI)
@pytest.fixture(autouse=True, scope="session")
def patch_fastapi_limiter():
    from unittest.mock import AsyncMock, patch
    mock_redis = AsyncMock()
    with patch("fastapi_limiter.FastAPILimiter.init", new=AsyncMock()), \
         patch("fastapi_limiter.FastAPILimiter.redis", new=mock_redis), \
         patch("fastapi_limiter.FastAPILimiter.identifier", new=AsyncMock(return_value="test_key")):
        yield

# 5. Auth Headers
@pytest.fixture()
def admin_headers():
    secret = os.getenv("JWT_SECRET", "testsecret123")
    payload = {
        "user_id": 1,
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture()
def user_headers():
    secret = os.getenv("JWT_SECRET", "testsecret123")
    payload = {
        "user_id": 2,
        "role": "user",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
