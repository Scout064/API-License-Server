import pytest

def test_create_client(client, admin_headers):
    response = client.post("/clients", json={"name": "Test", "email": "c@e.com"}, headers=admin_headers)
    assert response.status_code == 200

def test_generate_license(client, admin_headers):
    # Setup: Create and get the actual ID
    c_resp = client.post("/clients", json={"name": "Test", "email": "c@e.com"}, headers=admin_headers)
    client_id = c_resp.json()["id"]
    
    response = client.post(f"/licenses/generate?client_id={client_id}", headers=admin_headers)
    assert response.status_code == 200

def test_validate_license(client, admin_headers, reader_headers):
    # Setup
    c_resp = client.post("/clients", json={"name": "Test", "email": "c@e.com"}, headers=admin_headers)
    client_id = c_resp.json()["id"]
    gen_resp = client.post(f"/licenses/generate?client_id={client_id}", headers=admin_headers)
    real_key = gen_resp.json()["key"]

    # Action: Must use reader_headers to avoid 403 Forbidden 
    response = client.get(f"/licenses/{real_key}", headers=reader_headers)
    assert response.status_code == 200

def test_revoke_license(client, admin_headers):
    # Setup
    c_resp = client.post("/clients", json={"name": "Test", "email": "c@e.com"}, headers=admin_headers)
    client_id = c_resp.json()["id"]
    gen_resp = client.post(f"/licenses/generate?client_id={client_id}", headers=admin_headers)
    real_key = gen_resp.json()["key"]

    response = client.post(f"/licenses/{real_key}/revoke", headers=admin_headers)
    assert response.status_code == 200
