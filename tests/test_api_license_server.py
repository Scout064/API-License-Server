import pytest

# 1. Test Client Creation
def test_create_client(client, admin_headers):
    response = client.post(
        "/clients", 
        json={"name": "Test Client", "email": "client@example.com"}, 
        headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Client"

# 2. Test License Generation
def test_generate_license(client, admin_headers):
    # First, we MUST create a client so that client_id=1 actually exists
    client.post("/clients", json={"name": "Test", "email": "t@e.com"}, headers=admin_headers)
    
    # Now generate the license for that client
    response = client.post("/licenses/generate?client_id=1", headers=admin_headers)
    assert response.status_code == 200
    assert "key" in response.json()

# 3. Test License Validation (Fixes the 403 and the 404)
def test_validate_license(client, admin_headers, reader_headers):
    # Setup: Create client and generate a real key
    client.post("/clients", json={"name": "Test", "email": "t@e.com"}, headers=admin_headers)
    gen_resp = client.post("/licenses/generate?client_id=1", headers=admin_headers)
    real_key = gen_resp.json()["key"]

    # Action: Validate using reader_headers (Role: reader)
    # Using admin_headers here would cause a 403 based on your routes.py
    response = client.get(f"/licenses/{real_key}", headers=reader_headers)
    
    assert response.status_code == 200
    assert response.json()["key"] == real_key

# 4. Test License Revocation
def test_revoke_license(client, admin_headers):
    # Setup: Create client and generate a real key
    client.post("/clients", json={"name": "Test", "email": "t@e.com"}, headers=admin_headers)
    gen_resp = client.post("/licenses/generate?client_id=1", headers=admin_headers)
    real_key = gen_resp.json()["key"]

    # Action: Revoke
    response = client.post(f"/licenses/{real_key}/revoke", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "revoked"
