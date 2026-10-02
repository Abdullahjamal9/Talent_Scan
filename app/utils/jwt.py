import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from app.core.config import JWT_SECRET_KEY, JWT_EXPIRE_DAYS

ALGORITHM = "HS256"


def _secret() -> str:
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is not set")
    return JWT_SECRET_KEY


def create_jwt_token(data: dict, expires_delta: timedelta = timedelta(days=JWT_EXPIRE_DAYS)) -> str:
    """Creates a JWT token."""
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(to_encode, _secret(), algorithm=ALGORITHM)


def verify_jwt_token(token: str) -> dict:
    """Verifies and decodes a JWT token."""
    try:
        return jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
