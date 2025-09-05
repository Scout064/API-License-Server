from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# ----------------------------
# License Schemas
# ----------------------------

class LicenseBase(BaseModel):
    key: str
    status: str
    expires_at: Optional[datetime] = None
    client_id: Optional[int] = None


class LicenseCreate(LicenseBase):
    pass


class LicenseUpdate(BaseModel):
    key: Optional[str] = None
    status: Optional[str] = None
    expires_at: Optional[datetime] = None
    client_id: Optional[int] = None


class License(LicenseBase):
    id: int

    class Config:
        orm_mode = True


# ----------------------------
# Client Schemas
# ----------------------------

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
