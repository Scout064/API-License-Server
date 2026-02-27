from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")

if not all([DB_USER, DB_PASS, DB_NAME, DB_HOST]):
    raise RuntimeError("DB_USER, DB_PASS, DB_NAME, DB_HOST required")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
