# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base  # 假设你的 database.py 在 core 里，如果路径不同请调整

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")  # "user" 或 "admin"
    created_at = Column(DateTime(timezone=True), server_default=func.now())