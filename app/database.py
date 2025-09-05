# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# --- MariaDB Config ---
DB_USER = os.getenv("DB_USER", "license_user")
DB_PASS = os.getenv("DB_PASS", "StrongPassword123!")
DB_NAME = os.getenv("DB_NAME", "license_db")
DB_HOST = os.getenv("DB_HOST", "localhost")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# --- SQLAlchemy Engine & Session ---
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Dependency für FastAPI ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
