import random
import string
from fastapi import APIRouter, HTTPException, Depends, Path, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app import schemas
from app.database import get_db
from app.auth import require_role
from app.models import LicenseORM, ClientORM
from app.auth import hash_license_key

# Rate Limiter (10 per minute per IP)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

@router.exception_handler(RateLimitExceeded)
def ratelimit_handler(request: Request, exc: RateLimitExceeded):
    raise HTTPException(status_code=429, detail="Rate limit exceeded")

# -------------------
# Clients (admin only)
# -------------------
@router.post("/clients", response_model=schemas.Client)
@limiter.limit("5/minute")
def create_client(
    client: schemas.ClientCreate, db: Session = Depends(get_db), user=Depends(require_role("admin"))
):
    existing = db.query(ClientORM).filter(ClientORM.email == client.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Client exists")
    db_client = ClientORM(name=client.name, email=client.email)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.get("/clients", response_model=list[schemas.Client])
@limiter.limit("10/minute")
def list_clients(db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    return db.query(ClientORM).all()

@router.get("/clients/{client_id}", response_model=schemas.Client)
@limiter.limit("10/minute")
def get_client(
    client_id: int, db: Session = Depends(get_db), user=Depends(require_role("admin"))
):
    client = db.get(ClientORM, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Not found")
    return client

# -------------------
# Licenses
# -------------------
@router.post("/licenses/generate", response_model=schemas.License)
@limiter.limit("5/minute")
def create_license(
    client_id: int, db: Session = Depends(get_db), user=Depends(require_role("admin"))
):
    client = db.get(ClientORM, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    while True:
        key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        key_fmt = "-".join([key[i:i+4] for i in range(0,16,4)])
        hashed = hash_license_key(key_fmt)
        if not db.query(LicenseORM).filter(LicenseORM.key_hash == hashed).first():
            break
    new_license = LicenseORM(key_hash=hashed, client_id=client_id, status="active")
    db.add(new_license)
    db.commit()
    db.refresh(new_license)
    return {**new_license.__dict__, "key": key_fmt}

@router.get("/licenses/{license_key}", response_model=schemas.License)
@limiter.limit("10/minute")
def get_license(
    license_key: str = Path(...), db: Session = Depends(get_db), user=Depends(require_role("reader"))
):
    hashed = hash_license_key(license_key)
    lic = db.query(LicenseORM).filter(LicenseORM.key_hash == hashed).first()
    if not lic:
        raise HTTPException(status_code=404, detail="Not found")
    return {**lic.__dict__, "key": license_key}

@router.post("/licenses/{license_key}/revoke", response_model=schemas.License)
@limiter.limit("5/minute")
def revoke_license(
    license_key: str = Path(...), db: Session = Depends(get_db), user=Depends(require_role("admin"))
):
    hashed = hash_license_key(license_key)
    lic = db.query(LicenseORM).filter(LicenseORM.key_hash == hashed).first()
    if not lic:
        raise HTTPException(status_code=404, detail="Not found")
    if lic.status == "revoked":
        raise HTTPException(status_code=400, detail="Already revoked")
    lic.status = "revoked"
    db.commit()
    db.refresh(lic)
    return {**lic.__dict__, "key": license_key}
