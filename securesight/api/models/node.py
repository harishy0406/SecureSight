from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from securesight.api.core.database import Base, IdMixin, TimestampMixin


class Node(IdMixin, TimestampMixin, Base):
    __tablename__ = "nodes"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255))
    config: Mapped[dict | None] = mapped_column(JSON, default=dict)
