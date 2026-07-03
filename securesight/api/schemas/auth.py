from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=200)


class LoginRequest(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    type: str = "access"
    user_id: int | None = None
    tenant_id: int | None = None


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserPublic"  # noqa: F821


from securesight.api.schemas.user import UserPublic  # noqa: E402, F401
UserPublic.model_rebuild()
AuthResponse.model_rebuild()
