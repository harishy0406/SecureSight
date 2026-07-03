from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from securesight.api.core.database import Base, IdMixin, TimestampMixin


class AlertStatus(str, enum.Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"


class AlertHistory(IdMixin, TimestampMixin, Base):
    __tablename__ = "alert_history"

    value: Mapped[float] = mapped_column(Float, nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), default=AlertStatus.FIRING, nullable=False)
    fired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    alert_rule_id: Mapped[int] = mapped_column(ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False, index=True)

    alert_rule = relationship("AlertRule", back_populates="alert_history", lazy="selectin")
