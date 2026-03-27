import pytest
from datetime import datetime, timezone

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
    
    # Action: Generate license (Added &expiry=1_month)
    response = client.post(f"/licenses/generate?client_id={client_id}&expiry=1_month", headers=admin_headers)
    
    assert response.status_code == 200
    assert "key" in response.json()
    assert response.json()["status"] == "active"

def test_validate_license(client, admin_headers, reader_headers):
    """Tests GET /licenses/{license_key}"""
    # Setup: Create client -> Generate license
    c_resp = client.post("/clients", json={"name": "Val Client", "email": "val@example.com"}, headers=admin_headers)
    client_id = c_resp.json()["id"]
    
    # Added &expiry=1_month
    gen_resp = client.post(f"/licenses/generate?client_id={client_id}&expiry=1_month", headers=admin_headers)
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
    
    # Added &expiry=1_month
    gen_resp = client.post(f"/licenses/generate?client_id={client_id}&expiry=1_month", headers=admin_headers)
    real_key = gen_resp.json()["key"]

    # Action: Revoke
    response = client.post(f"/licenses/{real_key}/revoke", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "revoked"


# ==========================================
# EXTEND ROUTE
# ==========================================

def _setup_license(client, admin_headers):
    """Helper: create a client and generate a 1-month license. Returns (license_key, original_expires_at)."""
    c_resp = client.post("/clients", json={"name": "Ext Client", "email": "ext@example.com"}, headers=admin_headers)
    client_id = c_resp.json()["id"]
    gen_resp = client.post(f"/licenses/generate?client_id={client_id}&expiry=1_month", headers=admin_headers)
    data = gen_resp.json()
    return data["key"], data["expires_at"]


def test_extend_license_one_month(client, admin_headers):
    """Extending by 1_month adds ~30 days to the current expires_at."""
    key, original_expires_at = _setup_license(client, admin_headers)

    response = client.post(f"/licenses/{key}/extend?expiry=1_month", headers=admin_headers)
    assert response.status_code == 200

    original_dt = datetime.fromisoformat(original_expires_at.replace("Z", "+00:00")).replace(tzinfo=None)
    new_dt = datetime.fromisoformat(response.json()["expires_at"].replace("Z", "+00:00")).replace(tzinfo=None)
    delta_days = (new_dt - original_dt).days
    assert delta_days == 30


def test_extend_license_one_year(client, admin_headers):
    """Extending by 1_year adds 365 days to the current expires_at."""
    key, original_expires_at = _setup_license(client, admin_headers)

    response = client.post(f"/licenses/{key}/extend?expiry=1_year", headers=admin_headers)
    assert response.status_code == 200

    original_dt = datetime.fromisoformat(original_expires_at.replace("Z", "+00:00")).replace(tzinfo=None)
    new_dt = datetime.fromisoformat(response.json()["expires_at"].replace("Z", "+00:00")).replace(tzinfo=None)
    assert (new_dt - original_dt).days == 365


def test_extend_license_two_year(client, admin_headers):
    """Extending by 2_year adds 730 days to the current expires_at."""
    key, original_expires_at = _setup_license(client, admin_headers)

    response = client.post(f"/licenses/{key}/extend?expiry=2_year", headers=admin_headers)
    assert response.status_code == 200

    original_dt = datetime.fromisoformat(original_expires_at.replace("Z", "+00:00")).replace(tzinfo=None)
    new_dt = datetime.fromisoformat(response.json()["expires_at"].replace("Z", "+00:00")).replace(tzinfo=None)
    assert (new_dt - original_dt).days == 730


def test_extend_license_stacks(client, admin_headers):
    """Calling extend twice accumulates: remaining time is always preserved."""
    key, original_expires_at = _setup_license(client, admin_headers)

    client.post(f"/licenses/{key}/extend?expiry=1_month", headers=admin_headers)
    response = client.post(f"/licenses/{key}/extend?expiry=1_year", headers=admin_headers)
    assert response.status_code == 200

    original_dt = datetime.fromisoformat(original_expires_at.replace("Z", "+00:00")).replace(tzinfo=None)
    new_dt = datetime.fromisoformat(response.json()["expires_at"].replace("Z", "+00:00")).replace(tzinfo=None)
    assert (new_dt - original_dt).days == 30 + 365


def test_extend_license_not_found(client, admin_headers):
    """Returns 404 for a well-formatted but unknown license key."""
    response = client.post("/licenses/ZZZZ-ZZZZ-ZZZZ-ZZZZ/extend?expiry=1_month", headers=admin_headers)
    assert response.status_code == 404


def test_extend_license_requires_admin(client, reader_headers):
    """Returns 403 when called with a reader token."""
    response = client.post("/licenses/AAAA-BBBB-CCCC-DDDD/extend?expiry=1_month", headers=reader_headers)
    assert response.status_code == 403


def test_extend_license_requires_authentication(client):
    """Returns 403 when no Bearer token is supplied."""
    response = client.post("/licenses/AAAA-BBBB-CCCC-DDDD/extend?expiry=1_month")
    assert response.status_code == 403


def test_extend_license_invalid_expiry(client, admin_headers):
    """Returns 422 for an unrecognised expiry value."""
    key, _ = _setup_license(client, admin_headers)
    response = client.post(f"/licenses/{key}/extend?expiry=5_year", headers=admin_headers)
    assert response.status_code == 422


# ==========================================
# UNBIND ROUTE
# ==========================================

def test_unbind_license_clears_instance_id(client, admin_headers, make_reader_headers):
    """Owner client can unbind their own license's instance_id."""
    # Setup: create client, generate license, bind an instance
    c_resp = client.post("/clients", json={"name": "Unbind Client", "email": "unbind@example.com"}, headers=admin_headers)
    client_id = c_resp.json()["id"]
    reader_headers = make_reader_headers(client_id)

    gen_resp = client.post(f"/licenses/generate?client_id={client_id}&expiry=1_month", headers=admin_headers)
    real_key = gen_resp.json()["key"]

    # Bind an instance_id via GET validate
    client.get(f"/licenses/{real_key}?instance_id=my-machine-001", headers=reader_headers)

    # Confirm it's bound
    bound = client.get(f"/licenses/{real_key}", headers=reader_headers).json()
    assert bound["instance_id"] == "my-machine-001"

    # Action: unbind
    response = client.delete(f"/licenses/{real_key}/unbind", headers=reader_headers)
    assert response.status_code == 200
    assert response.json()["instance_id"] is None


def test_unbind_license_not_bound_returns_409(client, admin_headers, make_reader_headers):
    """Returns 409 if the license has no instance_id to unbind."""
    c_resp = client.post("/clients", json={"name": "No Bind Client", "email": "nobind@example.com"}, headers=admin_headers)
    client_id = c_resp.json()["id"]
    reader_headers = make_reader_headers(client_id)

    gen_resp = client.post(f"/licenses/generate?client_id={client_id}&expiry=1_month", headers=admin_headers)
    real_key = gen_resp.json()["key"]

    response = client.delete(f"/licenses/{real_key}/unbind", headers=reader_headers)
    assert response.status_code == 409
    assert "not bound" in response.json()["detail"]


def test_unbind_license_wrong_owner_returns_403(client, admin_headers, make_reader_headers):
    """A client cannot unbind a license that belongs to a different client."""
    # Client A owns the license
    c_a = client.post("/clients", json={"name": "Client A", "email": "a@example.com"}, headers=admin_headers).json()
    client_a_headers = make_reader_headers(c_a["id"])

    gen_resp = client.post(f"/licenses/generate?client_id={c_a['id']}&expiry=1_month", headers=admin_headers)
    real_key = gen_resp.json()["key"]

    # Bind an instance so unbind has something to do
    client.get(f"/licenses/{real_key}?instance_id=machine-abc", headers=client_a_headers)

    # Client B tries to unbind Client A's license
    c_b = client.post("/clients", json={"name": "Client B", "email": "b@example.com"}, headers=admin_headers).json()
    client_b_headers = make_reader_headers(c_b["id"])

    response = client.delete(f"/licenses/{real_key}/unbind", headers=client_b_headers)
    assert response.status_code == 403
    assert "do not own" in response.json()["detail"]


def test_unbind_license_admin_can_unbind_any(client, admin_headers, make_reader_headers):
    """Admin role can unbind any license regardless of ownership."""
    c_resp = client.post("/clients", json={"name": "Admin Target", "email": "admintgt@example.com"}, headers=admin_headers)
    client_id = c_resp.json()["id"]
    reader_headers = make_reader_headers(client_id)

    gen_resp = client.post(f"/licenses/generate?client_id={client_id}&expiry=1_month", headers=admin_headers)
    real_key = gen_resp.json()["key"]

    client.get(f"/licenses/{real_key}?instance_id=some-machine", headers=reader_headers)

    # Admin unbinds (admin JWT has no matching sub, but is_admin bypasses the check)
    response = client.delete(f"/licenses/{real_key}/unbind", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["instance_id"] is None


def test_unbind_license_not_found_returns_404(client, admin_headers, make_reader_headers):
    """Returns 404 for a well-formatted but non-existent license key."""
    headers = make_reader_headers(1)
    response = client.delete("/licenses/AAAA-BBBB-CCCC-DDDD/unbind", headers=headers)
    assert response.status_code == 404


def test_unbind_requires_authentication(client):
    """Returns 403 when no Bearer token is supplied."""
    response = client.delete("/licenses/AAAA-BBBB-CCCC-DDDD/unbind")
    assert response.status_code == 403
