from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=200)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    display_name: str | None = Field(None, max_length=200)
    avatar_url: str | None = None
    is_active: bool | None = None


class UserPublic(BaseModel):
    id: int
    email: str
    username: str
    display_name: str | None
    avatar_url: str | None
    status: str
    is_superuser: bool
    is_active: bool
    email_verified_at: datetime | None
    last_login_at: datetime | None
    role_id: int | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class UserInDB(UserPublic):
    hashed_password: str
