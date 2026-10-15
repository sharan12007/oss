"""Authentication routes: register, login, forgot/reset password."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone
from app.mongodb import get_users_collection, get_reset_tokens_collection
from app.auth_utils import (
    hash_password, verify_password,
    create_access_token, create_reset_token, decode_token,
    get_current_user,
)
import logging
import secrets

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth")


# ─── Request / Response Models ────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(default="", max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserProfile(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: str
    created_at: str


# ─── Register ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    """Register a new user account."""
    users = await get_users_collection()

    # Check if email already exists
    existing_email = await users.find_one({"email": req.email})
    if existing_email:
        raise HTTPException(409, "An account with this email already exists")

    # Check if username already exists
    existing_username = await users.find_one({"username": req.username.lower()})
    if existing_username:
        raise HTTPException(409, "This username is already taken")

    # Create user document
    now = datetime.now(timezone.utc)
    user_doc = {
        "username": req.username.lower(),
        "email": req.email.lower(),
        "password_hash": hash_password(req.password),
        "full_name": req.full_name or req.username,
        "created_at": now,
        "updated_at": now,
    }

    result = await users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    # Generate JWT
    token = create_access_token(user_id, req.email.lower(), req.username.lower())

    logger.info(f"New user registered: {req.username} ({req.email})")

    return AuthResponse(
        access_token=token,
        user={
            "user_id": user_id,
            "username": req.username.lower(),
            "email": req.email.lower(),
            "full_name": req.full_name or req.username,
        },
    )


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Authenticate user and return JWT token."""
    users = await get_users_collection()

    user = await users.find_one({"email": req.email.lower()})
    if not user:
        raise HTTPException(401, "Invalid email or password")

    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")

    user_id = str(user["_id"])
    token = create_access_token(user_id, user["email"], user["username"])

    logger.info(f"User logged in: {user['username']}")

    return AuthResponse(
        access_token=token,
        user={
            "user_id": user_id,
            "username": user["username"],
            "email": user["email"],
            "full_name": user.get("full_name", user["username"]),
        },
    )


# ─── Forgot Password ────────────────────────────────────────────────────────

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    """
    Generate a password reset token.
    In production, this would send an email. Here we return the token directly.
    """
    users = await get_users_collection()
    reset_tokens = await get_reset_tokens_collection()

    user = await users.find_one({"email": req.email.lower()})
    if not user:
        # Don't reveal whether email exists — always return success
        return {
            "success": True,
            "message": "If an account with that email exists, a reset code has been generated.",
        }

    # Generate a 6-digit OTP-style code + JWT reset token
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    reset_jwt = create_reset_token(req.email.lower())

    # Store the reset token in MongoDB
    await reset_tokens.delete_many({"email": req.email.lower()})
    await reset_tokens.insert_one({
        "email": req.email.lower(),
        "token": otp_code,
        "jwt_token": reset_jwt,
        "expires_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
    })

    logger.info(f"Password reset requested for: {req.email}")

    # In a real app, send email. For development, return the code directly.
    return {
        "success": True,
        "message": "If an account with that email exists, a reset code has been generated.",
        "reset_code": otp_code,  # Remove in production — send via email instead
        "reset_token": reset_jwt,  # Remove in production
    }


# ─── Reset Password ─────────────────────────────────────────────────────────

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    """Reset password using a valid reset token (OTP code or JWT)."""
    users = await get_users_collection()
    reset_tokens = await get_reset_tokens_collection()

    # Try OTP code first
    token_doc = await reset_tokens.find_one({"token": req.token})

    if token_doc:
        email = token_doc["email"]
    else:
        # Try decoding as JWT
        try:
            payload = decode_token(req.token)
            if payload.get("purpose") != "password_reset":
                raise HTTPException(400, "Invalid reset token")
            email = payload["email"]
        except Exception:
            raise HTTPException(400, "Invalid or expired reset token")

    # Update password
    result = await users.update_one(
        {"email": email},
        {
            "$set": {
                "password_hash": hash_password(req.new_password),
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    if result.modified_count == 0:
        raise HTTPException(404, "User not found")

    # Clean up used tokens
    await reset_tokens.delete_many({"email": email})

    logger.info(f"Password reset successful for: {email}")

    return {"success": True, "message": "Password has been reset successfully"}


# ─── User Profile ────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    users = await get_users_collection()
    from bson import ObjectId

    user = await users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        raise HTTPException(404, "User not found")

    return UserProfile(
        user_id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name", user["username"]),
        created_at=user["created_at"].isoformat(),
    )
