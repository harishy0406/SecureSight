from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from securesight.api.core.database import get_session
from securesight.api.dependencies import get_current_user
from securesight.api.models.user import User
from securesight.api.schemas.anomaly import AnomalyCreate, AnomalyEventPublic, AnomalyFeedbackCreate
from securesight.api.schemas.common import Message, PaginatedResponse
from securesight.api.services.anomaly_service import AnomalyService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[AnomalyEventPublic])
async def list_anomalies(
    page: int = 1,
    per_page: int = 50,
    severity: str | None = None,
    status: str | None = None,
    host_id: int | None = None,
    detector: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = AnomalyService(session)
    events, total = await service.get_all(
        page=page, per_page=per_page, severity=severity, status=status, host_id=host_id, detector=detector
    )
    return PaginatedResponse(
        items=[AnomalyEventPublic.model_validate(e) for e in events],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
    )


@router.get("/stats")
async def get_anomaly_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = AnomalyService(session)
    return await service.get_stats()


@router.get("/{anomaly_id}", response_model=AnomalyEventPublic)
async def get_anomaly(
    anomaly_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = AnomalyService(session)
    event = await service.get_by_id(anomaly_id)
    return AnomalyEventPublic.model_validate(event)


@router.post("/", response_model=AnomalyEventPublic, status_code=status.HTTP_201_CREATED)
async def create_anomaly(
    request: AnomalyCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = AnomalyService(session)
    event = await service.create(request)
    return AnomalyEventPublic.model_validate(event)


@router.post("/{anomaly_id}/feedback", response_model=AnomalyEventPublic)
async def submit_feedback(
    anomaly_id: int,
    request: AnomalyFeedbackCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = AnomalyService(session)
    event = await service.submit_feedback(anomaly_id, request)
    return AnomalyEventPublic.model_validate(event)


@router.delete("/{anomaly_id}", response_model=Message)
async def delete_anomaly(
    anomaly_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = AnomalyService(session)
    await service.delete(anomaly_id)
    return Message(detail="Anomaly event deleted")
