import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

# Konfiguration aus ENV Variablen
SECRET_KEY = os.getenv("JWT_SECRET", "CHANGE_ME_SUPER_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

# OAuth2 Schema
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# -------------------------
# Hilfsfunktionen
# -------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Erstellt ein signiertes JWT Token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str) -> bool:
    """Prüft Benutzername/Passwort gegen ENV Variablen."""
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


# -------------------------
# Dependencies
# -------------------------

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Prüft JWT Token und gibt User zurück."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username != ADMIN_USERNAME:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"username": username}


# -------------------------
# Router für Auth
# -------------------------

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login mit Benutzername & Passwort, gibt JWT zurück."""
    if not authenticate_user(form_data.username, form_data.password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}
