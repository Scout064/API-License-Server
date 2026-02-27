from fastapi import FastAPI
from app.routes import router
from app.database import engine, Base
from app import models  # IMPORTANT: ensures models are registered

app = FastAPI(
    title="License Server API",
    description="API for license generation, validation, and revocation",
    version="1.0.0"
)

# Create tables on startup
Base.metadata.create_all(bind=engine)

app.include_router(router)
