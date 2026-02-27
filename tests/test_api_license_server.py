import pytest

# ==========================================
# CLIENT ROUTES
# ==========================================

def test_create_client(client, admin_headers):
    """Tests POST /clients"""
    response = client.post(
        "/clients", 
        json={"name": "Test Client", "email": "create@example.com"}, 
        headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Client"

def test_list_clients(client, admin_headers):
    """Tests GET /clients"""
    # Setup: Create a couple of clients
    client.post("/clients", json={"name": "Client 1", "email": "c1@example.com"}, headers=admin_headers)
    client.post("/clients", json={"name": "Client 2", "email": "c2@example.com"}, headers=admin_headers)
    
    # Action: Fetch the list
    response = client.get("/clients", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

def test_get_client(client, admin_headers):
    """Tests GET /clients/{client_id}"""
    # Setup: Create a client and get their ID
    c_resp = client.post("/clients", json={"name": "Target Client", "email": "target@example.com"}, headers=admin_headers)
    client_id = c_resp.json()["id"]
    
    # Action: Fetch that specific client
    response = client.get(f"/clients/{client_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == client_id
    assert response.json()["name"] == "Target Client"

def test_get_client_not_found(client, admin_headers):
    """Tests GET /clients/{client_id} for a non-existent client"""
    # Action: Try to fetch a client ID that doesn't exist (9999)
    response = client.get("/clients/9999", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found"


# ==========================================
# LICENSE ROUTES
# ==========================================

def test_generate_license(client, admin_headers):
    """Tests POST /licenses/generate"""
    # Setup: Create client
    c_resp = client.post("/clients", json={"name": "Gen Client", "email": "gen@example.com"}, headers=admin_headers)
    client_id = c_resp.json()["id"]
    
    # Action: Generate license
    response = client.post(f"/licenses/generate?client_id={client_id}", headers=admin_headers)
    assert response.status_code == 200
    assert "key" in response.json()
    assert response.json()["status"] == "active"

def test_validate_license(client, admin_headers, reader_headers):
    """Tests GET /licenses/{license_key}"""
    # Setup: Create client -> Generate license
    c_resp = client.post("/clients", json={"name": "Val Client", "email": "val@example.com"}, headers=admin_headers)
    client_id = c_resp.json()["id"]
    gen_resp = client.post(f"/licenses/generate?client_id={client_id}", headers=admin_headers)
    real_key = gen_resp.json()["key"]

    # Action: Validate (Requires reader role)
    response = client.get(f"/licenses/{real_key}", headers=reader_headers)
    assert response.status_code == 200
    assert response.json()["key"] == real_key
    assert response.json()["status"] == "active"

def test_revoke_license(client, admin_headers):
    """Tests POST /licenses/{license_key}/revoke"""
    # Setup: Create client -> Generate license
    c_resp = client.post("/clients", json={"name": "Rev Client", "email": "rev@example.com"}, headers=admin_headers)
    client_id = c_resp.json()["id"]
    gen_resp = client.post(f"/licenses/generate?client_id={client_id}", headers=admin_headers)
    real_key = gen_resp.json()["key"]

    # Action: Revoke
    response = client.post(f"/licenses/{real_key}/revoke", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "revoked"
