# tests/test_api_license_server.py

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import jwt
from app.main import app
from app.models import LicenseORM, ClientORM
from app.auth import JWT_SECRET  # your JWT secret from auth.py
import os

os.environ["DB_USER"] = "test_user"
os.environ["DB_PASS"] = "test_pass"
os.environ["DB_NAME"] = "test_db"
os.environ["DB_HOST"] = "localhost"

client = TestClient(app)

# Utility to create test JWT token for admin
def create_admin_token():
    payload = {
        "sub": 1,
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(minutes=60)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

admin_headers = {"Authorization": f"Bearer {create_admin_token()}"}

@pytest.mark.parametrize("name,email", [("Test Client","client@example.com")])
def test_create_client(name, email):
    response = client.post("/clients", json={"name": name, "email": email}, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == name
    assert data["email"] == email
    assert "id" in data

@pytest.mark.parametrize("client_id", [1])
def test_generate_license(client_id):
    response = client.post(f"/licenses/generate?client_id={client_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == client_id
    assert data["status"] == "active"
    assert "key" in data

@pytest.mark.parametrize("license_key", ["ABCD-1234-EFGH-5678"])
def test_validate_license(license_key):
    headers = admin_headers  # reader/admin token can be used
    response = client.get(f"/licenses/{license_key}", headers=headers)
    assert response.status_code in [200, 404]

@pytest.mark.parametrize("license_key", ["ABCD-1234-EFGH-5678"])
def test_revoke_license(license_key):
    headers = admin_headers
    response = client.post(f"/licenses/{license_key}/revoke", headers=headers)
    assert response.status_code in [200, 404]
