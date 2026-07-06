"""認証 API。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.config import settings
from src.core.auth.jwt_handler import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_hours: int


class AuthStatusResponse(BaseModel):
    auth_enabled: bool
    openai_configured: bool


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status():
    return AuthStatusResponse(
        auth_enabled=settings.auth_enabled,
        openai_configured=settings.openai_configured,
    )


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT_SECRET is not configured",
        )
    if body.username != settings.auth_username or body.password != settings.auth_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(body.username)
    return LoginResponse(
        access_token=token,
        expires_in_hours=settings.jwt_expire_hours,
    )
