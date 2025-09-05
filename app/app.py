from __future__ import annotations

import os
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated, Literal

from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import (
    create_engine, String, Text, DateTime, Boolean, Integer, ForeignKey, Enum, select, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_SUPER_SECRET")
JWT_ALG = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./licenses.db")

DEFAULT_ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "changeme")  # change immediately in prod!

# -----------------------------------------------------------------------------
# Database setup
# -----------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class LicenseStatus:
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"

from sqlalchemy import Enum as SAEnum
class License(Base):
    __tablename__ = "licenses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    product_code: Mapped[str] = mapped_column(String(64), index=True)
    owner: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    status: Mapped[str] = mapped_column(SAEnum(LicenseStatus.ACTIVE, LicenseStatus.REVOKED, name="lic_status"), default=LicenseStatus.ACTIVE)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # free-form metadata

engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
Base.metadata.create_all(engine)

# -----------------------------------------------------------------------------
# Security / Auth
# -----------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token",
    scopes={"admin": "Full administrative access to license management."},
)

def create_default_admin():
    with Session(engine) as s:
        existing = s.scalar(select(User).where(User.username == DEFAULT_ADMIN_USER))
        if not existing:
            u = User(
                username=DEFAULT_ADMIN_USER,
                password_hash=pwd_context.hash(DEFAULT_ADMIN_PASS),
                is_admin=True,
            )
            s.add(u)
            s.commit()

create_default_admin()

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list[str] = []

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    is_admin: bool
    created_at: datetime

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def authenticate_user(username: str, password: str) -> Optional[User]:
    with Session(engine) as s:
        user = s.scalar(select(User).where(User.username == username))
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALG)
    return encoded_jwt, expire

async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        username: str = payload.get("sub")
        scopes: list[str] = payload.get("scopes", [])
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token: missing subject.")
        token_data = TokenData(username=username, scopes=scopes)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token.")

    with Session(engine) as s:
        user = s.scalar(select(User).where(User.username == token_data.username))
        if not user:
            raise HTTPException(status_code=401, detail="User not found.")

        # Check requested scopes
        for scope in security_scopes.scopes:
            if scope == "admin" and not user.is_admin:
                raise HTTPException(status_code=403, detail="Insufficient permissions: admin scope required.")
        return user

def require_admin(user: Annotated[User, Security(get_current_user, scopes=["admin"])]):
    return user

# -----------------------------------------------------------------------------
# Pydantic Schemas for API
# -----------------------------------------------------------------------------
class LicenseCreate(BaseModel):
    product_code: str = Field(..., examples=["MYAPP-PRO"])
    owner: Optional[str] = Field(None, examples=["customer@example.com"])
    expires_in_days: Optional[int] = Field(None, ge=1, le=10_000)
    note: Optional[str] = Field(None, description="Optional note / metadata")

class LicenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    product_code: str
    owner: Optional[str]
    status: Literal["ACTIVE", "REVOKED"]
    issued_at: datetime
    revoked_at: Optional[datetime]
    expires_at: Optional[datetime]
    note: Optional[str]

class LicenseValidateIn(BaseModel):
    key: str = Field(..., min_length=8)
    product_code: Optional[str] = None

class LicenseValidateOut(BaseModel):
    valid: bool
    reason: Optional[str] = None
    license: Optional[LicenseOut] = None

class LicenseRevokeIn(BaseModel):
    reason: Optional[str] = Field(None, description="Optional reason recorded in note")

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def generate_license_key(length: int = 28) -> str:
    # URL-safe segmented key, e.g. XXXX-XXXX-XXXX-XXXX-XXXX
    alphabet = string.ascii_uppercase + string.digits
    raw = "".join(secrets.choice(alphabet) for _ in range(length))
    parts = [raw[i:i+5] for i in range(0, len(raw), 5)]
    return "-".join(parts)

# -----------------------------------------------------------------------------
# FastAPI app (OpenAPI docs auto-generated)
# -----------------------------------------------------------------------------
app = FastAPI(
    title="License Server",
    version="1.0.0",
    description="""
API-driven license server with JWT authentication.

### Authentication
- Obtain a bearer token via **POST /auth/token** using form fields `username` & `password` (OAuth2 password flow).
- Admin-only endpoints require the `admin` scope.

### Licenses
- **POST /licenses** (admin): Create a license.
- **POST /licenses/{key}/revoke** (admin): Revoke a license.
- **GET /licenses/{key}** (admin): Inspect a license.
- **GET /licenses** (admin): List/search licenses.
- **POST /licenses/validate** (public): Validate a license key.
"""
)

# -----------------------------------------------------------------------------
# Auth endpoints
# -----------------------------------------------------------------------------
@app.post("/auth/token", response_model=Token, summary="Obtain access token (JWT)")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    scopes = ["admin"] if user.is_admin else []
    token, exp = create_access_token({"sub": user.username, "scopes": scopes})
    return Token(access_token=token, expires_in=int((exp - datetime.now(timezone.utc)).total_seconds()))

@app.get("/users/me", response_model=UserOut, summary="Get current user")
async def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

# -----------------------------------------------------------------------------
# License endpoints
# -----------------------------------------------------------------------------
@app.post("/licenses", response_model=LicenseOut, summary="Create a license", tags=["licenses"])
async def create_license(payload: LicenseCreate, _: Annotated[User, Depends(require_admin)]):
    expires_at = None
    if payload.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)

    key = generate_license_key()
    lic = License(
        key=key,
        product_code=payload.product_code,
        owner=payload.owner,
        expires_at=expires_at,
        status=LicenseStatus.ACTIVE,
        note=payload.note,
    )
    with Session(engine) as s:
        s.add(lic)
        s.commit()
        s.refresh(lic)
        return lic

@app.get("/licenses", response_model=list[LicenseOut], summary="List/search licenses", tags=["licenses"])
async def list_licenses(
    _: Annotated[User, Depends(require_admin)],
    product_code: Optional[str] = None,
    owner: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    stmt = select(License).order_by(License.id.desc())
    if product_code:
        stmt = stmt.where(License.product_code == product_code)
    if owner:
        stmt = stmt.where(License.owner == owner)
    if status_filter in (LicenseStatus.ACTIVE, LicenseStatus.REVOKED):
        stmt = stmt.where(License.status == status_filter)

    with Session(engine) as s:
        rows = s.scalars(stmt.limit(limit).offset(offset)).all()
        return rows

@app.get("/licenses/{key}", response_model=LicenseOut, summary="Get a license by key", tags=["licenses"])
async def get_license(key: str, _: Annotated[User, Depends(require_admin)]):
    with Session(engine) as s:
        lic = s.scalar(select(License).where(License.key == key))
        if not lic:
            raise HTTPException(status_code=404, detail="License not found")
        return lic

@app.post("/licenses/{key}/revoke", response_model=LicenseOut, summary="Revoke a license", tags=["licenses"])
async def revoke_license(key: str, payload: LicenseRevokeIn, _: Annotated[User, Depends(require_admin)]):
    with Session(engine) as s:
        lic = s.scalar(select(License).where(License.key == key))
        if not lic:
            raise HTTPException(status_code=404, detail="License not found")
        if lic.status == LicenseStatus.REVOKED:
            return lic
        lic.status = LicenseStatus.REVOKED
        lic.revoked_at = datetime.now(timezone.utc)
        if payload.reason:
            # append reason to note
            if lic.note:
                lic.note = f"{lic.note}\nRevoked: {payload.reason}"
            else:
                lic.note = f"Revoked: {payload.reason}"
        s.add(lic)
        s.commit()
        s.refresh(lic)
        return lic

@app.post("/licenses/validate", response_model=LicenseValidateOut, summary="Validate a license key", tags=["licenses"])
async def validate_license(payload: LicenseValidateIn):
    with Session(engine) as s:
        lic = s.scalar(select(License).where(License.key == payload.key))
        if not lic:
            return LicenseValidateOut(valid=False, reason="NOT_FOUND")

        if payload.product_code and lic.product_code != payload.product_code:
            return LicenseValidateOut(valid=False, reason="PRODUCT_MISMATCH")

        if lic.status != LicenseStatus.ACTIVE:
            return LicenseValidateOut(valid=False, reason="REVOKED")

        if lic.expires_at and lic.expires_at < datetime.now(timezone.utc):
            return LicenseValidateOut(valid=False, reason="EXPIRED", license=lic)

        return LicenseValidateOut(valid=True, license=lic)
