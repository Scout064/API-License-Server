# tests/test_api_license_server.py

import pytest
from datetime import datetime, timedelta
from app.models import hash_license_key, generate_license_key, LicenseORM, ClientORM


def test_generate_license_key_format():
    key = generate_license_key()
    assert len(key) == 19  # format XXXX-XXXX-XXXX-XXXX
    assert key.count('-') == 3


def test_hash_license_key():
    key = 'ABCD-1234-EFGH-5678'
    hashed = hash_license_key(key)
    assert hashed != key
    assert len(hashed) == 64  # SHA-256 hex digest length


def test_license_model_creation():
    client = ClientORM(id=1, name='Test Client', email='client@example.com')
    key = generate_license_key()
    license_hash = hash_license_key(key)
    license_obj = LicenseORM(
        id=1,
        key_hash=license_hash,
        client_id=client.id,
        status='active',
        expires_at=datetime.utcnow() + timedelta(days=30),
        client=client
    )

    assert license_obj.key_hash == license_hash
    assert license_obj.status == 'active'
    assert license_obj.client == client
