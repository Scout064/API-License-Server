"""
app/models.py
"""
from datetime import datetime
from typing import Optional, List
import hashlib
import secrets
import string
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from app.database import Base 

def hash_license_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def generate_license_key(length: int = 16) -> str:
    alphabet = string.ascii_uppercase + string.digits
    raw = "".join(secrets.choice(alphabet) for _ in range(length))
    return "-".join(raw[i:i + 4] for i in range(0, length, 4))

# --- New Utility for Client Secrets ---
def generate_client_secret(length: int = 32) -> str:
    """Generates a secure random string for use as a client secret."""
    return secrets.token_urlsafe(length)

class ClientORM(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    
    # --- New Fields for App Authentication ---
    client_id = Column(String(255), unique=True, index=True, nullable=False)
    hashed_secret = Column(String(255), nullable=False)
    role = Column(String(50), default="reader") 
    
    created_at = Column(DateTime, default=datetime.utcnow)
    licenses = relationship("LicenseORM", back_populates="client", cascade="all, delete-orphan")

class LicenseORM(Base):
    __tablename__ = "licenses"
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"))
    status = Column(Enum("active", "revoked", name="license_status"), default="active", nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    client = relationship("ClientORM", back_populates="licenses")

# --- Pydantic Schemas ---
class ClientBase(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str] = "reader"

class ClientCreate(ClientBase):
    pass

class ClientResponse(ClientBase):
    id: int
    client_id: str
    client_secret: Optional[str] = None # Only returned once during creation
    created_at: datetime
    class Config:
        from_attributes = True

class LicenseBase(BaseModel):
    client_id: int
    expires_at: Optional[datetime] = None

class License(LicenseBase):
    id: int
    status: str
    created_at: datetime
    key: Optional[str] = None 
    class Config:
        from_attributes = True
