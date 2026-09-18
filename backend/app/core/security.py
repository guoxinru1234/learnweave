# backend/app/core/security.py
import os
from werkzeug.security import generate_password_hash, check_password_hash
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "c52db9c8fbacad0ed006fb50f6d8f537542ea343e7d0b03ce2f34e11a27d0df4")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

def get_password_hash(password: str) -> str:
    # pbkdf2:sha256 快且安全，避免 scrypt 在 Windows 多线程卡顿
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # check_password_hash 自动识别 hash 前缀，兼容旧的 scrypt 密码
    return check_password_hash(hashed_password, plain_password)

# 其余 JWT 部分保持不变
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
