from fastapi import FastAPI
from app.routes import router
app = FastAPI(title="License Server API")
app.include_router(router, prefix="/api")
