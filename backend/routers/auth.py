from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone, timedelta
from jose import jwt
import uuid

from ..config import SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from ..data_store import user_store
from ..websocket.ai.services.models.schemas import (
    RegisterRequest, LoginRequest, AuthTokenResponse,
    ForgotPasswordRequest, ResetPasswordRequest
)
from ..websocket.ai.services.email_service import send_otp_email

import random
import time

OTP_STORE = {} # Format: { "email": {"otp": "123456", "expires_at": timestamp} }

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=AuthTokenResponse)
async def register(body: RegisterRequest):
    # Check if username already exists
    if user_store.get_by_username(body.username):
        raise HTTPException(400, "Username already exists")

    # In a real app, hash the password. We use plaintext for this MVP.
    new_user = {
        "id": f"u-{uuid.uuid4().hex[:8]}",
        "username": body.username,
        "email": body.email,
        "password": body.password,
        "role": body.role
    }
    
    user_store.add_user(new_user)
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    token = jwt.encode(
        {"sub": new_user["username"], "role": new_user["role"], "exp": expire},
        SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    
    return AuthTokenResponse(
        token=token,
        username=new_user["username"],
        role=new_user["role"],
        expires_in=JWT_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=AuthTokenResponse)
async def login(body: LoginRequest):
    user = user_store.get_by_username(body.username)
    if not user:
        raise HTTPException(401, "Invalid username or password")
        
    if user["password"] != body.password:
        raise HTTPException(401, "Invalid username or password")
        
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    token = jwt.encode(
        {"sub": user["username"], "role": user["role"], "exp": expire},
        SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    
    return AuthTokenResponse(
        token=token,
        username=user["username"],
        role=user["role"],
        expires_in=JWT_EXPIRE_MINUTES * 60,
    )

@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    # For MVP: Directly update the password without OTP
    user = user_store.get_by_username(body.username)
    if not user:
        raise HTTPException(404, "User not found")
        
    success = user_store.update_password(body.username, body.new_password)
    if not success:
        raise HTTPException(500, "Failed to update password.")
        
    return {"message": "Password successfully updated."}


@router.get("/users")
async def get_all_users():
    # In a real app, verify admin JWT token here.
    return user_store.get_all()


