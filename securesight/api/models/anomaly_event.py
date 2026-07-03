from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from securesight.api.core.database import Base, IdMixin, TimestampMixin


class AnomalySeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnomalyStatus(str, enum.Enum):
    NEW = "new"
    REVIEWING = "reviewing"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    RESOLVED = "resolved"


class AnomalyEvent(IdMixin, TimestampMixin, Base):
    __tablename__ = "anomaly_events"

    metric_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    observed_value: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_value: Mapped[float | None] = mapped_column(Float)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[AnomalySeverity] = mapped_column(Enum(AnomalySeverity), default=AnomalySeverity.MEDIUM, nullable=False)
    status: Mapped[AnomalyStatus] = mapped_column(Enum(AnomalyStatus), default=AnomalyStatus.NEW, nullable=False)
    detector: Mapped[str] = mapped_column(String(100), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    context: Mapped[dict | None] = mapped_column(JSON, default=dict)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False, index=True)

    host = relationship("Host", back_populates="anomaly_events", lazy="selectin")
