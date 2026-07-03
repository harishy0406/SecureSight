from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select

from securesight.api.core.logging import get_logger
from securesight.api.models.dashboard import Dashboard
from securesight.api.services.base import BaseService

logger = get_logger(__name__)


class DashboardService(BaseService):
    async def get_all(
        self,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[Dashboard], int]:
        query = select(Dashboard)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Dashboard.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_by_id(self, dashboard_id: int) -> Dashboard:
        result = await self.session.execute(select(Dashboard).where(Dashboard.id == dashboard_id))
        dashboard = result.scalar_one_or_none()
        if dashboard is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
        return dashboard

    async def create(self, request) -> Dashboard:
        dashboard = Dashboard(**request.model_dump())
        return await self.commit_and_refresh(dashboard)

    async def update(self, dashboard_id: int, request) -> Dashboard:
        dashboard = await self.get_by_id(dashboard_id)
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(dashboard, field, value)
        await self.session.flush()
        await self.session.refresh(dashboard)
        return dashboard

    async def delete(self, dashboard_id: int) -> None:
        dashboard = await self.get_by_id(dashboard_id)
        await self.session.delete(dashboard)
        await self.session.flush()
