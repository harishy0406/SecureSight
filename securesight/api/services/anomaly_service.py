from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select

from securesight.api.core.logging import get_logger
from securesight.api.models.anomaly_event import AnomalyEvent, AnomalySeverity, AnomalyStatus
from securesight.api.schemas.anomaly import AnomalyCreate, AnomalyFeedbackCreate
from securesight.api.services.base import BaseService

logger = get_logger(__name__)


class AnomalyService(BaseService):
    async def create(self, request: AnomalyCreate) -> AnomalyEvent:
        event = AnomalyEvent(
            metric_name=request.metric_name,
            observed_value=request.observed_value,
            predicted_value=request.predicted_value,
            anomaly_score=request.anomaly_score,
            severity=request.severity,
            detector=request.detector,
            explanation=request.explanation,
            context=request.context,
            host_id=request.host_id,
        )
        return await self.commit_and_refresh(event)

    async def get_all(
        self,
        page: int = 1,
        per_page: int = 50,
        severity: str | None = None,
        status: str | None = None,
        host_id: int | None = None,
        detector: str | None = None,
    ) -> tuple[list[AnomalyEvent], int]:
        query = select(AnomalyEvent)
        if severity:
            query = query.where(AnomalyEvent.severity == severity)
        if status:
            query = query.where(AnomalyEvent.status == status)
        if host_id:
            query = query.where(AnomalyEvent.host_id == host_id)
        if detector:
            query = query.where(AnomalyEvent.detector == detector)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AnomalyEvent.detected_at.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_by_id(self, anomaly_id: int) -> AnomalyEvent:
        result = await self.session.execute(select(AnomalyEvent).where(AnomalyEvent.id == anomaly_id))
        event = result.scalar_one_or_none()
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly event not found")
        return event

    async def submit_feedback(self, anomaly_id: int, request: AnomalyFeedbackCreate) -> AnomalyEvent:
        event = await self.get_by_id(anomaly_id)
        event.status = request.status
        event.resolved_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def get_stats(self) -> dict:
        total_result = await self.session.execute(select(func.count(AnomalyEvent.id)))
        total = total_result.scalar() or 0

        severity_result = await self.session.execute(
            select(AnomalyEvent.severity, func.count(AnomalyEvent.id)).group_by(AnomalyEvent.severity)
        )
        severity_counts = {sev: cnt for sev, cnt in severity_result.all()}

        pending_result = await self.session.execute(
            select(func.count(AnomalyEvent.id)).where(AnomalyEvent.status == AnomalyStatus.PENDING)
        )
        pending = pending_result.scalar() or 0

        return {
            "total": total,
            "by_severity": severity_counts,
            "pending_review": pending,
        }

    async def delete(self, anomaly_id: int) -> None:
        event = await self.get_by_id(anomaly_id)
        await self.session.delete(event)
        await self.session.flush()
