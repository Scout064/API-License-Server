import pytest

@pytest.mark.parametrize("name,email", [("Test Client","client@example.com")])
def test_create_client(name, email, client, admin_headers):
    response = client.post("/clients", json={"name": name, "email": email}, headers=admin_headers)
    assert response.status_code == 200

@pytest.mark.parametrize("client_id", [1])
def test_generate_license(client_id, client, admin_headers):
    response = client.post(f"/licenses/generate?client_id={client_id}", headers=admin_headers)
    assert response.status_code == 200

@pytest.mark.parametrize("license_key", ["ABCD-1234-EFGH-5678"])
def test_validate_license(license_key, client, admin_headers):
    response = client.get(f"/licenses/{license_key}", headers=admin_headers)
    assert response.status_code in [200, 404]

@pytest.mark.parametrize("license_key", ["ABCD-1234-EFGH-5678"])
def test_revoke_license(license_key, client, admin_headers):
    response = client.post(f"/licenses/{license_key}/revoke", headers=admin_headers)
    assert response.status_code in [200, 404]
