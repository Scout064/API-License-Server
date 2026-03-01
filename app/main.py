from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import router
from app.database import engine, Base
from app import models  # IMPORTANT: ensures models are registered
from dotenv import load_dotenv
load_dotenv("/var/www/licenseapi/.env")

# Import Redis and the Limiter
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter

# Define startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis connection for rate limiting
    redis_connection = redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_connection)
    
    yield # App runs here
    
    # Shutdown: Close Redis connection
    await redis_connection.close()

# Pass the lifespan context to FastAPI
app = FastAPI(
    title="License Server API",
    description="API for license generation, validation, and revocation",
    version="2.0.0",
    lifespan=lifespan
)

# Create tables on startup
Base.metadata.create_all(bind=engine)

app.include_router(router)
