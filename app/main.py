from fastapi import FastAPI
from app.routes import router
from app.auth import router as auth_router

app = FastAPI(
    title="License Server API",
    description="API for license generation, validation, and revocation",
    version="1.0.0"
)

# Auth-Router hinzufügen
app.include_router(auth_router)

app.include_router(router, prefix="/api")
