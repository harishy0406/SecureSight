from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select

from securesight.api.core.logging import get_logger
from securesight.api.models.host import Host
from securesight.api.models.metric import Metric
from securesight.api.schemas.metric import MetricCreate
from securesight.api.services.base import BaseService

logger = get_logger(__name__)


class MetricService(BaseService):
    async def ingest(self, request: MetricCreate, host_id: int) -> Metric:
        result = await self.session.execute(select(Host).where(Host.id == host_id))
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

        metric = Metric(
            name=request.name,
            value=request.value,
            unit=request.unit,
            tags=request.tags,
            host_id=host_id,
            recorded_at=request.recorded_at or datetime.utcnow(),
        )
        return await self.commit_and_refresh(metric)

    async def query(
        self,
        name: str | None = None,
        host_id: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page: int = 1,
        per_page: int = 100,
    ) -> tuple[list[Metric], int]:
        query = select(Metric)
        if name:
            query = query.where(Metric.name == name)
        if host_id:
            query = query.where(Metric.host_id == host_id)
        if start_time:
            query = query.where(Metric.recorded_at >= start_time)
        if end_time:
            query = query.where(Metric.recorded_at <= end_time)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Metric.recorded_at.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_latest(self, name: str, host_id: int | None = None) -> Metric | None:
        query = select(Metric).where(Metric.name == name)
        if host_id:
            query = query.where(Metric.host_id == host_id)
        query = query.order_by(Metric.recorded_at.desc()).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_aggregation(
        self,
        name: str,
        host_id: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict:
        query = select(
            func.avg(Metric.value).label("avg"),
            func.min(Metric.value).label("min"),
            func.max(Metric.value).label("max"),
            func.count(Metric.id).label("count"),
        ).where(Metric.name == name)
        if host_id:
            query = query.where(Metric.host_id == host_id)
        if start_time:
            query = query.where(Metric.recorded_at >= start_time)
        if end_time:
            query = query.where(Metric.recorded_at <= end_time)
        result = await self.session.execute(query)
        row = result.one()
        return {
            "name": name,
            "avg": row.avg,
            "min": row.min,
            "max": row.max,
            "count": row.count,
        }
