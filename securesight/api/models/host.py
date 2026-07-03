from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from securesight.api.core.database import Base, IdMixin, TimestampMixin


class HostStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class HostType(str, enum.Enum):
    SERVER = "server"
    CONTAINER = "container"
    VIRTUAL_MACHINE = "virtual_machine"
    NETWORK_DEVICE = "network_device"
    EDGE_DEVICE = "edge_device"


class Host(IdMixin, TimestampMixin, Base):
    __tablename__ = "hosts"

    hostname: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    os: Mapped[str | None] = mapped_column(String(100))
    os_version: Mapped[str | None] = mapped_column(String(100))
    host_type: Mapped[HostType] = mapped_column(Enum(HostType), default=HostType.SERVER, nullable=False)
    status: Mapped[HostStatus] = mapped_column(Enum(HostStatus), default=HostStatus.UNKNOWN, nullable=False)
    cpu_cores: Mapped[int | None] = mapped_column()
    memory_total_mb: Mapped[int | None] = mapped_column()
    disk_total_gb: Mapped[float | None] = mapped_column(Float)
    tags: Mapped[dict | None] = mapped_column(JSON, default=dict)
    agent_version: Mapped[str | None] = mapped_column(String(50))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    metrics = relationship("Metric", back_populates="host", lazy="selectin", cascade="all, delete-orphan")
    alert_rules = relationship("AlertRule", back_populates="host", lazy="selectin", cascade="all, delete-orphan")
    anomaly_events = relationship("AnomalyEvent", back_populates="host", lazy="selectin", cascade="all, delete-orphan")
