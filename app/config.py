import os

# Database configuration
DB_USER = os.getenv("DB_USER", "license_user")
DB_PASS = os.getenv("DB_PASS", "StrongPassword123!")
DB_NAME = os.getenv("DB_NAME", "license_db")
DB_HOST = os.getenv("DB_HOST", "localhost")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_SUPER_SECRET")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# Admin credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")
