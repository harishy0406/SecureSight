from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select

from securesight.api.core.logging import get_logger
from securesight.api.models.host import Host, HostStatus, HostType
from securesight.api.schemas.host import HostCreate, HostUpdate
from securesight.api.services.base import BaseService

logger = get_logger(__name__)


class HostService(BaseService):
    async def get_all(
        self,
        page: int = 1,
        per_page: int = 50,
        status: str | None = None,
        host_type: str | None = None,
    ) -> tuple[list[Host], int]:
        query = select(Host)
        if status:
            query = query.where(Host.status == status)
        if host_type:
            query = query.where(Host.host_type == host_type)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Host.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_by_id(self, host_id: int) -> Host:
        result = await self.session.execute(select(Host).where(Host.id == host_id))
        host = result.scalar_one_or_none()
        if host is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
        return host

    async def create(self, request: HostCreate) -> Host:
        existing = await self.session.execute(select(Host).where(Host.hostname == request.hostname))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Hostname already exists")

        host = Host(**request.model_dump())
        return await self.commit_and_refresh(host)

    async def update(self, host_id: int, request: HostUpdate) -> Host:
        host = await self.get_by_id(host_id)
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(host, field, value)
        host.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(host)
        return host

    async def delete(self, host_id: int) -> None:
        host = await self.get_by_id(host_id)
        await self.session.delete(host)
        await self.session.flush()

    async def update_heartbeat(self, host_id: int) -> Host:
        host = await self.get_by_id(host_id)
        host.last_seen_at = datetime.now(timezone.utc)
        if host.status == HostStatus.OFFLINE:
            host.status = HostStatus.ONLINE
        await self.session.flush()
        return host

    async def get_status_counts(self) -> dict[str, int]:
        result = await self.session.execute(
            select(Host.status, func.count(Host.id)).group_by(Host.status)
        )
        return {status: count for status, count in result.all()}
