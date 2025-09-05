from pydantic import BaseModel
from datetime import datetime

# --- Request Models ---
class LicenseRequest(BaseModel):
    license_key: str

class LicenseCreateRequest(BaseModel):
    user_id: int
    product_id: int
    expires_at: datetime  # ISO 8601 date string

class LicenseRevokeRequest(BaseModel):
    license_key: str


# --- Response Models ---
class LicenseValidationResponse(BaseModel):
    license_key: str
    valid: bool

class LicenseCreateResponse(BaseModel):
    id: int
    license_key: str
    status: str

class LicenseRevokeResponse(BaseModel):
    license_key: str
    status: str
