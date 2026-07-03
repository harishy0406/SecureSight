from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from securesight.api.core.database import get_session
from securesight.api.dependencies import get_current_user
from securesight.api.models.user import User
from securesight.api.schemas.common import Message, PaginatedResponse
from securesight.api.schemas.metric import MetricCreate, MetricPublic, MetricQueryParams
from securesight.api.services.metric_service import MetricService

router = APIRouter()


@router.post("/ingest", response_model=MetricPublic, status_code=status.HTTP_201_CREATED)
async def ingest_metric(
    request: MetricCreate,
    host_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = MetricService(session)
    metric = await service.ingest(request, host_id)
    return MetricPublic.model_validate(metric)


@router.get("/", response_model=PaginatedResponse[MetricPublic])
async def query_metrics(
    params: MetricQueryParams = Depends(),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = MetricService(session)
    metrics, total = await service.query(
        name=params.name,
        host_id=params.host_id,
        start_time=params.start_time,
        end_time=params.end_time,
        page=params.page,
        per_page=params.per_page,
    )
    return PaginatedResponse(
        items=[MetricPublic.model_validate(m) for m in metrics],
        total=total,
        page=params.page,
        per_page=params.per_page,
        total_pages=(total + params.per_page - 1) // params.per_page,
    )


@router.get("/latest/{name}")
async def get_latest_metric(
    name: str,
    host_id: int | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = MetricService(session)
    metric = await service.get_latest(name, host_id)
    if metric is None:
        return {"metric_name": name, "value": None}
    return MetricPublic.model_validate(metric)


@router.get("/aggregate/{name}")
async def get_aggregation(
    name: str,
    host_id: int | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = MetricService(session)
    return await service.get_aggregation(name, host_id, start_time, end_time)
