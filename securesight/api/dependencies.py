from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import (
    APIKeyHeader,
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from securesight.api.core.config import Settings, get_settings
from securesight.api.core.database import get_session
from securesight.api.core.logging import get_logger
from securesight.api.core.security import decode_token, verify_api_key
from securesight.api.models.api_key import ApiKey, ApiKeyStatus
from securesight.api.models.user import User, UserStatus

logger = get_logger(__name__)

reusable_oauth2 = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(reusable_oauth2),
    api_key: str | None = Security(api_key_header),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User:
    if api_key:
        result = await session.execute(
            select(ApiKey).where(
                ApiKey.status == ApiKeyStatus.ACTIVE,
            )
        )
        for ak in result.scalars().all():
            if verify_api_key(api_key, ak.key_hash):
                if ak.expires_at and ak.expires_at < datetime.now(timezone.utc):
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key expired")
                ak.last_used_at = datetime.now(timezone.utc)
                await session.flush()
                result = await session.execute(select(User).where(User.id == ak.user_id))
                user = result.scalar_one_or_none()
                if user is not None and user.status == UserStatus.ACTIVE:
                    return user
                break

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user_id = int(user_id_str)
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is not active")
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Security(reusable_oauth2),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User | None:
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        result = await session.execute(select(User).where(User.id == int(user_id_str)))
        return result.scalar_one_or_none()
    except Exception:
        return None


async def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser access required")
    return current_user


async def get_settings_dependency() -> Settings:
    return get_settings()
