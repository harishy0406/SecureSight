from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HostCreate(BaseModel):
    hostname: str = Field(..., max_length=255)
    ip_address: str | None = Field(None, max_length=45)
    os: str | None = Field(None, max_length=100)
    os_version: str | None = Field(None, max_length=100)
    host_type: str = "server"
    cpu_cores: int | None = None
    memory_total_mb: int | None = None
    disk_total_gb: float | None = None
    tags: dict | None = None


class HostUpdate(BaseModel):
    hostname: str | None = Field(None, max_length=255)
    ip_address: str | None = None
    os: str | None = None
    os_version: str | None = None
    status: str | None = None
    cpu_cores: int | None = None
    memory_total_mb: int | None = None
    disk_total_gb: float | None = None
    tags: dict | None = None
    agent_version: str | None = None
    is_active: bool | None = None


class HostPublic(BaseModel):
    id: int
    hostname: str
    ip_address: str | None
    os: str | None
    os_version: str | None
    host_type: str
    status: str
    cpu_cores: int | None
    memory_total_mb: int | None
    disk_total_gb: float | None
    tags: dict | None
    agent_version: str | None
    last_seen_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class HostInDB(HostPublic):
    pass


class HostStatusCount(BaseModel):
    status: str
    count: int
