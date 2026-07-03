from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Message(BaseModel):
    detail: str
    code: str | None = None


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=500)
    sort_by: str | None = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int


class TimestampSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
