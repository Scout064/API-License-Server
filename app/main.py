from fastapi import FastAPI
from app.routes import router

app = FastAPI(
    title="License Server API",
    description="API for license generation, validation, and revocation",
    version="1.0.0"
)

app.include_router(router)
