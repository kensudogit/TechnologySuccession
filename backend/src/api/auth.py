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
    username: str = "admin"
    using_default_password: bool = True


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status():
    return AuthStatusResponse(
        auth_enabled=settings.auth_enabled,
        openai_configured=settings.openai_configured,
        username=settings.auth_username,
        using_default_password=settings.auth_password == "admin",
    )


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT_SECRET is not configured",
        )
    username = body.username.strip()
    password = body.password.strip()
    if username != settings.auth_username or password != settings.auth_password:
        hint = (
            "ユーザー名またはパスワードが正しくありません。"
            if settings.auth_password == "admin"
            else (
                "ユーザー名またはパスワードが正しくありません。"
                " Railway の AUTH_PASSWORD が admin 以外に設定されています。"
            )
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=hint,
        )
    token = create_access_token(username)
    return LoginResponse(
        access_token=token,
        expires_in_hours=settings.jwt_expire_hours,
    )
