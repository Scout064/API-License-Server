from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import License
import uuid
router = APIRouter()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@router.post("/licenses/")
def create_license(user_id: str, db: Session = Depends(get_db)):
    key = str(uuid.uuid4())
    license = License(license_key=key, user_id=user_id)
    db.add(license)
    db.commit()
    db.refresh(license)
    return {"license_key": key}
@router.post("/licenses/validate")
def validate_license(license_key: str, db: Session = Depends(get_db)):
    license = db.query(License).filter(License.license_key == license_key).first()
    if not license or license.status != "active":
        raise HTTPException(status_code=400, detail="Invalid license")
    return {"valid": True}
@router.post("/licenses/revoke/{license_key}")
def revoke_license(license_key: str, db: Session = Depends(get_db)):
    license = db.query(License).filter(License.license_key == license_key).first()
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    license.status = "revoked"
    db.commit()
    return {"revoked": True}