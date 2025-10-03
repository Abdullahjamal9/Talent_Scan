import jwt
import os
from datetime import datetime, timedelta
from fastapi import HTTPException, status

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "test-secret-key")
ALGORITHM = "HS256"

def create_jwt_token(data: dict, expires_delta: timedelta = timedelta(days=30)) -> str:
    """Creates a JWT token."""
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    """Verifies and decodes a JWT token."""
    try:
        print(token)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )
