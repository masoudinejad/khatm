import hashlib
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import settings

security = HTTPBearer()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=settings.token_expiry_days),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security), conn=None) -> int:
    """Verify token and check if user is admin"""
    user_id = verify_token(credentials)

    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection required")

    cursor = conn.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    if not result or not result[0]:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    return user_id
