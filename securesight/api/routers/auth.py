from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from securesight.api.core.config import Settings, get_settings
from securesight.api.core.database import get_session
from securesight.api.dependencies import get_current_user
from securesight.api.models.user import User
from securesight.api.schemas.auth import AuthResponse, LoginRequest, RefreshTokenRequest, RegisterRequest
from securesight.api.schemas.common import Message
from securesight.api.schemas.user import UserPublic
from securesight.api.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, session: AsyncSession = Depends(get_session), settings: Settings = Depends(get_settings)):
    service = AuthService(session, settings)
    return await service.register(request)


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, session: AsyncSession = Depends(get_session), settings: Settings = Depends(get_settings)):
    service = AuthService(session, settings)
    return await service.login(request)


@router.post("/refresh", response_model=AuthResponse)
async def refresh(request: RefreshTokenRequest, session: AsyncSession = Depends(get_session), settings: Settings = Depends(get_settings)):
    service = AuthService(session, settings)
    return await service.refresh_token(request.refresh_token)


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserPublic.model_validate(current_user)


@router.post("/change-password", response_model=Message)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    service = AuthService(session, settings)
    await service.update_password(current_user.id, current_password, new_password)
    return Message(detail="Password changed successfully")
