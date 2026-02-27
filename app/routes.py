from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from app.models import ClientBase, Client, LicenseBase, License, hash_license_key
from app.database import get_db
from app.auth import require_role
from fastapi_limiter.depends import RateLimiter
import secrets

router = APIRouter()

LICENSE_KEY_REGEX = r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'

# ------------------- CLIENT ROUTES -------------------

@router.post("/clients", response_model=Client, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def create_client(client: ClientBase, db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    db_client = ClientORM(name=client.name, email=client.email)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.get("/clients", response_model=list[Client])
def list_clients(db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    return db.query(ClientORM).all()

@router.get("/clients/{client_id}", response_model=Client)
def get_client(client_id: int, db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    db_client = db.query(ClientORM).filter(ClientORM.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client

# ------------------- LICENSE ROUTES -------------------

@router.post("/licenses/generate", response_model=License, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def generate_license(client_id: int, db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    client = db.query(ClientORM).filter(ClientORM.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # generate license key
    key_fmt = '-'.join([''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(4)) for _ in range(4)])
    hashed = hash_license_key(key_fmt)

    db_license = LicenseORM(key_hash=hashed, client_id=client_id, status='active')
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    
    return License(id=db_license.id, client_id=client_id, status=db_license.status, key=key_fmt, created_at=db_license.created_at)

@router.get("/licenses/{license_key}", response_model=License, dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def validate_license(license_key: str = Path(..., pattern=LICENSE_KEY_REGEX), db: Session = Depends(get_db), user=Depends(require_role("reader"))):
    hashed = hash_license_key(license_key)
    license_obj = db.query(LicenseORM).filter(LicenseORM.key_hash == hashed).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    return License(id=license_obj.id, client_id=license_obj.client_id, status=license_obj.status, key=license_key, created_at=license_obj.created_at)

@router.post("/licenses/{license_key}/revoke", response_model=License, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def revoke_license(license_key: str = Path(..., pattern=LICENSE_KEY_REGEX), db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    hashed = hash_license_key(license_key)
    license_obj = db.query(LicenseORM).filter(LicenseORM.key_hash == hashed).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    license_obj.status = 'revoked'
    db.commit()
    db.refresh(license_obj)
    return License(id=license_obj.id, client_id=license_obj.client_id, status=license_obj.status, key=license_key, created_at=license_obj.created_at)
