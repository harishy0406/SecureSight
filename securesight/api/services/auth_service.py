from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select

from securesight.api.core.config import Settings
from securesight.api.core.logging import get_logger
from securesight.api.core.security import create_access_token, create_refresh_token, decode_token
from securesight.api.models.user import User, UserStatus
from securesight.api.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from securesight.api.schemas.user import UserPublic
from securesight.api.services.base import BaseService

logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService(BaseService):
    def __init__(self, session, settings: Settings) -> None:
        super().__init__(session)
        self.settings = settings

    async def register(self, request: RegisterRequest) -> AuthResponse:
        existing = await self.session.execute(
            select(User).where(
                (User.email == request.email) | (User.username == request.username)
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already exists")

        user = User(
            email=request.email,
            username=request.username,
            hashed_password=pwd_context.hash(request.password),
            display_name=request.display_name or request.username,
        )
        await self.commit_and_refresh(user)
        return await self._build_auth_response(user)

    async def login(self, request: LoginRequest) -> AuthResponse:
        if request.email:
            stmt = select(User).where(User.email == request.email)
        elif request.username:
            stmt = select(User).where(User.username == request.username)
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email or username required")

        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None or not pwd_context.verify(request.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not active")

        user.last_login_at = datetime.now(timezone.utc)
        await self.session.flush()
        return await self._build_auth_response(user)

    async def refresh_token(self, token: str) -> AuthResponse:
        try:
            payload = decode_token(token, expected_type="refresh")
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        result = await self.session.execute(select(User).where(User.id == int(sub), User.status == UserStatus.ACTIVE))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return await self._build_auth_response(user)

    async def _build_auth_response(self, user: User) -> AuthResponse:
        settings = self.settings
        access_token = create_access_token(
            str(user.id),
            extra_claims={"user_id": user.id},
        )
        refresh_token = create_refresh_token(
            str(user.id),
            extra_claims={"user_id": user.id},
        )
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=UserPublic.model_validate(user),
        )

    async def get_user_by_id(self, user_id: int) -> User:
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    async def update_password(self, user_id: int, current_password: str, new_password: str) -> None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if not pwd_context.verify(current_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
        user.hashed_password = pwd_context.hash(new_password)
        await self.session.flush()
