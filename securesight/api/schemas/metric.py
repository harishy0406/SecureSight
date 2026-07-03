from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MetricCreate(BaseModel):
    name: str = Field(..., max_length=255)
    value: float
    unit: str | None = Field(None, max_length=50)
    tags: dict | None = None
    recorded_at: datetime | None = None


class MetricPublic(BaseModel):
    id: int
    name: str
    value: float
    unit: str | None
    tags: dict | None
    host_id: int
    recorded_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricInDB(MetricPublic):
    pass


class MetricQueryParams(BaseModel):
    name: str | None = None
    host_id: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=100, ge=1, le=1000)
