from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# ----------------------------
# SQLAlchemy ORM
# ----------------------------

class LicenseORM(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String(64), unique=True, nullable=False)
    user_id = Column(String(64), nullable=True)
    status = Column(Enum('active', 'revoked', name="license_status"), default='active', nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    revoked_at = Column(TIMESTAMP, nullable=True)


# ----------------------------
# Pydantic Schemas
# ----------------------------

class LicenseBase(BaseModel):
    license_key: str
    user_id: Optional[str] = None
    status: Optional[str] = 'active'
    revoked_at: Optional[datetime] = None


class LicenseCreate(LicenseBase):
    pass


class LicenseUpdate(BaseModel):
    license_key: Optional[str] = None
    user_id: Optional[str] = None
    status: Optional[str] = None
    revoked_at: Optional[datetime] = None


class License(LicenseBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
