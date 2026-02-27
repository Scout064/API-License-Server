"""
app/models.py

Database ORM models and Pydantic schemas.
Implements secure license key hashing and generation.
"""

from datetime import datetime
from typing import Optional, List

import hashlib
import secrets
import string

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship, declarative_base

from pydantic import BaseModel, EmailStr


Base = declarative_base()


# ==========================================================
# Utility Functions
# ==========================================================

def hash_license_key(key: str) -> str:
    """
    Hash license key using SHA-256.
    Only hashed values are stored in DB.
    """
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def generate_license_key(length: int = 16) -> str:
    """
    Generate secure license key formatted XXXX-XXXX-XXXX-XXXX.
    """
    alphabet = string.ascii_uppercase + string.digits
    raw = "".join(secrets.choice(alphabet) for _ in range(length))
    return "-".join(raw[i:i + 4] for i in range(0, length, 4))


# ==========================================================
# ORM MODELS
# ==========================================================

class ClientORM(Base):
    """
    Database model for API clients.
    """
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    licenses = relationship(
        "LicenseORM",
        back_populates="client",
        cascade="all, delete-orphan"
    )


class LicenseORM(Base):
    """
    Database model for licenses.
    Stores only hashed license keys.
    """
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)

    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"))
    status = Column(
        Enum("active", "revoked", name="license_status"),
        default="active",
        nullable=False,
    )
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("ClientORM", back_populates="licenses")


# ==========================================================
# Pydantic Schemas
# ==========================================================

# -------- Clients --------

class ClientBase(BaseModel):
    name: str
    email: EmailStr


class ClientCreate(ClientBase):
    pass


class Client(ClientBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# -------- Licenses --------

class LicenseBase(BaseModel):
    client_id: int
    expires_at: Optional[datetime] = None


class LicenseCreate(LicenseBase):
    pass


class License(LicenseBase):
    id: int
    status: str
    created_at: datetime
    key: Optional[str] = None  # returned only on generation

    class Config:
        from_attributes = True


class LicenseStatus(BaseModel):
    status: str
