from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# ----------------------------
# SQLAlchemy ORM Models
# ----------------------------

class LicenseORM(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    key = Column("license_key", String(64), unique=True, nullable=False, doc="License key in format XXXX-XXXX-XXXX-XXXX")
    client_id = Column(Integer, nullable=True, doc="Reference to client id")
    status = Column(Enum("active", "revoked"), default="active", doc="License status")
    created_at = Column(DateTime, default=datetime.utcnow, doc="Timestamp when license was created")
    revoked_at = Column(DateTime, nullable=True, doc="Timestamp when license was revoked")
    expires_at = Column(DateTime, nullable=True, doc="License expiration timestamp")


class ClientORM(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True, doc="Client ID")
    name = Column(String(128), nullable=False, doc="Client full name")
    email = Column(String(128), nullable=False, unique=True, doc="Client email address")


# ----------------------------
# Pydantic Schemas
# ----------------------------

# License Schemas
class LicenseBase(BaseModel):
    key: str = Field(..., description="License key in format XXXX-XXXX-XXXX-XXXX")
    status: str = Field(..., description="License status: active or revoked")
    client_id: Optional[int] = Field(None, description="ID of the client associated with the license")
    expires_at: Optional[datetime] = Field(None, description="Expiration date of the license")

class LicenseCreate(LicenseBase):
    pass

class LicenseUpdate(BaseModel):
    key: Optional[str] = Field(None, description="Updated license key")
    status: Optional[str] = Field(None, description="Updated status: active or revoked")
    client_id: Optional[int] = Field(None, description="Updated client id")
    expires_at: Optional[datetime] = Field(None, description="Updated expiration date")

class License(LicenseBase):
    id: int = Field(..., description="Unique license ID")

    class Config:
        orm_mode = True


# Client Schemas
class ClientBase(BaseModel):
    name: str = Field(..., description="Full name of the client")
    email: EmailStr = Field(..., description="Client email address")

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Updated client name")
    email: Optional[EmailStr] = Field(None, description="Updated client email address")

class Client(ClientBase):
    id: int = Field(..., description="Unique client ID")

    class Config:
        orm_mode = True
