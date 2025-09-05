from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter()

# ----------------------------
# License Endpoints
# ----------------------------

@router.post("/licenses", response_model=schemas.License)
def create_license(license: schemas.LicenseCreate, db: Session = Depends(get_db)):
    db_license = models.License(
        key=license.key,
        status=license.status,
        expires_at=license.expires_at,
        client_id=license.client_id,
    )
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license


@router.get("/licenses", response_model=list[schemas.License])
def list_licenses(db: Session = Depends(get_db)):
    return db.query(models.License).all()


@router.get("/licenses/{license_id}", response_model=schemas.License)
def get_license(license_id: int, db: Session = Depends(get_db)):
    db_license = db.query(models.License).filter(models.License.id == license_id).first()
    if not db_license:
        raise HTTPException(status_code=404, detail="License not found")
    return db_license


@router.put("/licenses/{license_id}", response_model=schemas.License)
def update_license(license_id: int, license: schemas.LicenseUpdate, db: Session = Depends(get_db)):
    db_license = db.query(models.License).filter(models.License.id == license_id).first()
    if not db_license:
        raise HTTPException(status_code=404, detail="License not found")

    for key, value in license.dict(exclude_unset=True).items():
        setattr(db_license, key, value)

    db.commit()
    db.refresh(db_license)
    return db_license


@router.delete("/licenses/{license_id}")
def delete_license(license_id: int, db: Session = Depends(get_db)):
    db_license = db.query(models.License).filter(models.License.id == license_id).first()
    if not db_license:
        raise HTTPException(status_code=404, detail="License not found")

    db.delete(db_license)
    db.commit()
    return {"detail": "License deleted successfully"}


# ----------------------------
# Client Endpoints
# ----------------------------

@router.post("/clients", response_model=schemas.Client)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    db_client = models.Client(
        name=client.name,
        email=client.email,
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


@router.get("/clients", response_model=list[schemas.Client])
def list_clients(db: Session = Depends(get_db)):
    return db.query(models.Client).all()


@router.get("/clients/{client_id}", response_model=schemas.Client)
def get_client(client_id: int, db: Session = Depends(get_db)):
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client


@router.put("/clients/{client_id}", response_model=schemas.Client)
def update_client(client_id: int, client: schemas.ClientUpdate, db: Session = Depends(get_db)):
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    for key, value in client.dict(exclude_unset=True).items():
        setattr(db_client, key, value)

    db.commit()
    db.refresh(db_client)
    return db_client


@router.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    db.delete(db_client)
    db.commit()
    return {"detail": "Client deleted successfully"}
