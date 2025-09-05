from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP
from app.database import Base
class License(Base):
    __tablename__ = "licenses"
    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(64))
    status = Column(Enum('active', 'revoked'), default='active')
    created_at = Column(TIMESTAMP)
    revoked_at = Column(TIMESTAMP, nullable=True)