from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.orm import Session
import random
import string
from typing import List

from app.database import get_db   # <-- make sure this exists
from app import models            # ORM models
from app import models as schemas # Pydantic schemas are in models.py

router = APIRouter()

# Regex pattern for license key: XXXX-XXXX-XXXX-XXXX
LICENSE_KEY_REGEX = r"^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$"

def generate_license_key() -> str:
    """Generates a license key in the format XXXX-XXXX-XXXX-XXXX"""
    parts = [''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(4)]
    return '-'.join(parts)

# -------------------
# Client Endpoints
# -------------------

@router.post("/api/clients", response_model=schemas.Client)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    """
    Create a new client.
    """
    existing = db.query(models.ClientORM).filter(models.ClientORM.email == client.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Client with this email already exists")
    
    db_client = models.ClientORM(name=client.name, email=client.email)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.get("/api/clients", response_model=List[schemas.Client])
def list_clients(db: Session = Depends(get_db)):
    """
    List all clients.
    """
    return db.query(models.ClientORM).all()

@router.get("/api/clients/{client_id}", response_model=schemas.Client)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """
    Get client by ID.
    """
    client = db.query(models.ClientORM).filter(models.ClientORM.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

# -------------------
# License Endpoints
# -------------------

@router.post("/api/licenses/generate", response_model=schemas.License)
def create_license(client_id: int, db: Session = Depends(get_db)):
    """
    Generate a new license key for a client.
    """
    client = db.query(models.ClientORM).filter(models.ClientORM.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Ensure unique license key
    while True:
        key = generate_license_key()
        if not db.query(models.LicenseORM).filter(models.LicenseORM.key == key).first():
            break

    new_license = models.LicenseORM(
        key=key,
        client_id=client_id,
        status="active"
    )
    db.add(new_license)
    db.commit()
    db.refresh(new_license)
    return new_license

@router.get("/api/licenses/{license_key}", response_model=schemas.License)
def get_license(
    license_key: str = Path(..., regex=LICENSE_KEY_REGEX),
    db: Session = Depends(get_db)
):
    """
    Get license info by license key.
    """
    license_obj = db.query(models.LicenseORM).filter(models.LicenseORM.key == license_key).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    return license_obj

@router.post("/api/licenses/{license_key}/revoke", response_model=schemas.License)
def revoke_license(
    license_key: str = Path(..., regex=LICENSE_KEY_REGEX),
    db: Session = Depends(get_db)
):
    """
    Revoke a license by key.
    """
    license_obj = db.query(models.LicenseORM).filter(models.LicenseORM.key == license_key).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    
    if license_obj.status == "revoked":
        raise HTTPException(status_code=400, detail="License already revoked")
    
    license_obj.status = "revoked"
    db.commit()
    db.refresh(license_obj)
    return license_obj
