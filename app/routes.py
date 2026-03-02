from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from app.models import ClientBase, Client, LicenseBase, License, hash_license_key, ClientORM, LicenseORM, hash_client_secret
from app.database import get_db
from app.auth import require_role, create_token, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi_limiter.depends import RateLimiter
import secrets

router = APIRouter()

LICENSE_KEY_REGEX = r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'

# ------------------- CLIENT ROUTES -------------------

@router.post("/clients", response_model=Client, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def create_client(client: ClientBase, db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    existing = db.query(ClientORM).filter(ClientORM.email == client.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Client already exists")
    # Required because secret_hash is NOT NULL
    raw_secret = secrets.token_hex(32)
    db_client = ClientORM(name=client.name, email=client.email, secret_hash=hash_client_secret(raw_secret))
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return {
        "id": db_client.id,
        "name": db_client.name,
        "email": db_client.email,
        "client_secret": raw_secret,  # returned only once
        "created_at": db_client.created_at,
    }

@router.get("/clients", response_model=list[Client])
def list_clients(db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    return db.query(ClientORM).all()

@router.get("/clients/{client_id}", response_model=Client)
def get_client(client_id: int, db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    db_client = db.query(ClientORM).filter(ClientORM.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client

@router.delete("/clients/{client_id}", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def delete_client(client_id: int, db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    db_client = db.query(ClientORM).filter(ClientORM.id == client_id).first()
    
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    # This single delete command will safely cascade to the licenses table
    db.delete(db_client)
    db.commit()

    return {"detail": f"Client {client_id} and all associated licenses successfully deleted"}

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

# ------------------- AUTH ROUTES FOR CLIENTS -------------------

@router.post("/auth/client-token")
def issue_client_token(
    client_id: int,
    client_secret: str,
    db: Session = Depends(get_db),
):
    client = db.query(ClientORM).filter(ClientORM.id == client_id).first()
    if not client:
        raise HTTPException(status_code=401, detail="Invalid client")

    if client.secret_hash != hash_client_secret(client_secret):
        raise HTTPException(status_code=401, detail="Invalid secret")

    token = create_token(user_id=client.id, role="reader")

    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
