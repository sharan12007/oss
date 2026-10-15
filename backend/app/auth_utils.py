"""Authentication utilities: JWT tokens, password hashing, dependency injection."""

import bcrypt
import jwt
import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import get_settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


# ─── Password Hashing ────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ─── JWT Token Management ────────────────────────────────────────────────────

def create_access_token(user_id: str, email: str, username: str) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    payload = {
        "sub": user_id,
        "email": email,
        "username": username,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_reset_token(email: str) -> str:
    """Create a short-lived JWT token for password reset."""
    settings = get_settings()
    payload = {
        "email": email,
        "purpose": "password_reset",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


# ─── FastAPI Dependency ──────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """FastAPI dependency: extract current user from JWT Bearer token."""
    if credentials is None:
        raise HTTPException(401, "Authentication required")
    
    payload = decode_token(credentials.credentials)
    return {
        "user_id": payload["sub"],
        "email": payload["email"],
        "username": payload["username"],
    }


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    """FastAPI dependency: optionally extract current user (returns None if not authenticated)."""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        return {
            "user_id": payload["sub"],
            "email": payload["email"],
            "username": payload["username"],
        }
    except HTTPException:
        return None
