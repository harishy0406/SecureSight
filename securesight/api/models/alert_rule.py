from __future__ import annotations

import enum

from sqlalchemy import JSON, Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy import JSON

from securesight.api.core.database import Base, IdMixin, TimestampMixin


class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertCondition(str, enum.Enum):
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUAL_TO = "equal_to"
    NOT_EQUAL = "not_equal"
    OUTSIDE_RANGE = "outside_range"
    INSIDE_RANGE = "inside_range"
    ANOMALY = "anomaly"
    NO_DATA = "no_data"


class AlertRule(IdMixin, TimestampMixin, Base):
    __tablename__ = "alert_rules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    condition: Mapped[AlertCondition] = mapped_column(Enum(AlertCondition), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_high: Mapped[float | None] = mapped_column(Float)
    severity: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity), default=AlertSeverity.MEDIUM, nullable=False)
    evaluation_window_seconds: Mapped[int] = mapped_column(Integer, default=300)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=600)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict | None] = mapped_column(JSON, default=dict)
    escalation_policy: Mapped[dict | None] = mapped_column(JSON, default=None)

    host_id: Mapped[int | None] = mapped_column(ForeignKey("hosts.id", ondelete="CASCADE"), index=True)

    host = relationship("Host", back_populates="alert_rules", lazy="selectin")
    alert_history = relationship("AlertHistory", back_populates="alert_rule", lazy="selectin", cascade="all, delete-orphan")
