from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter()


@router.post("/licenses", response_model=models.License)
def create_license(license: models.LicenseCreate, db: Session = Depends(get_db)):
    db_license = models.LicenseORM(
        license_key=license.license_key,
        user_id=license.user_id,
        status=license.status,
        revoked_at=license.revoked_at
    )
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license


@router.get("/licenses", response_model=list[models.License])
def list_licenses(db: Session = Depends(get_db)):
    return db.query(models.LicenseORM).all()


@router.get("/licenses/{license_id}", response_model=models.License)
def get_license(license_id: int, db: Session = Depends(get_db)):
    db_license = db.query(models.LicenseORM).filter(models.LicenseORM.id == license_id).first()
    if not db_license:
        raise HTTPException(status_code=404, detail="License not found")
    return db_license


@router.put("/licenses/{license_id}", response_model=models.License)
def update_license(license_id: int, license: models.LicenseUpdate, db: Session = Depends(get_db)):
    db_license = db.query(models.LicenseORM).filter(models.LicenseORM.id == license_id).first()
    if not db_license:
        raise HTTPException(status_code=404, detail="License not found")

    for key, value in license.dict(exclude_unset=True).items():
        setattr(db_license, key, value)

    db.commit()
    db.refresh(db_license)
    return db_license


@router.delete("/licenses/{license_id}")
def delete_license(license_id: int, db: Session = Depends(get_db)):
    db_license = db.query(models.LicenseORM).filter(models.LicenseORM.id == license_id).first()
    if not db_license:
        raise HTTPException(status_code=404, detail="License not found")

    db.delete(db_license)
    db.commit()
    return {"detail": "License deleted successfully"}
