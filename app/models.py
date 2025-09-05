from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# ----------------------------
# SQLAlchemy ORM Models
# ----------------------------

class LicenseORM(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String(64), unique=True, nullable=False)
    user_id = Column(String(64), nullable=True)
    status = Column(Enum("active", "revoked"), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)


class ClientORM(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False, unique=True)


# ----------------------------
# Pydantic Schemas
# ----------------------------

# License Schemas
class LicenseBase(BaseModel):
    key: str
    status: str
    expires_at: Optional[datetime] = None
    client_id: Optional[str] = None

class LicenseCreate(LicenseBase):
    pass

class LicenseUpdate(BaseModel):
    key: Optional[str] = None
    status: Optional[str] = None
    expires_at: Optional[datetime] = None
    client_id: Optional[str] = None

class License(LicenseBase):
    id: int

    class Config:
        orm_mode = True


# Client Schemas
class ClientBase(BaseModel):
    name: str
    email: EmailStr

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class Client(ClientBase):
    id: int

    class Config:
        orm_mode = True
