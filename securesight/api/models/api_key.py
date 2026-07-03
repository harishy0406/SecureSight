from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from securesight.api.core.database import Base, IdMixin, TimestampMixin


class ApiKeyStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ApiKey(IdMixin, TimestampMixin, Base):
    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[ApiKeyStatus] = mapped_column(Enum(ApiKeyStatus), default=ApiKeyStatus.ACTIVE, nullable=False)
    permissions: Mapped[dict | None] = mapped_column(JSON, default=dict)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    user = relationship("User", back_populates="api_keys", lazy="selectin")
