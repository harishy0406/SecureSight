from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from securesight.api.core.database import get_session
from securesight.api.dependencies import get_current_user
from securesight.api.models.user import User
from securesight.api.schemas.common import Message, PaginatedResponse
from securesight.api.schemas.host import HostCreate, HostPublic, HostStatusCount, HostUpdate
from securesight.api.services.host_service import HostService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[HostPublic])
async def list_hosts(
    page: int = 1,
    per_page: int = 50,
    status: str | None = None,
    host_type: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = HostService(session)
    hosts, total = await service.get_all(page=page, per_page=per_page, status=status, host_type=host_type)
    return PaginatedResponse(
        items=[HostPublic.model_validate(h) for h in hosts],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
    )


@router.get("/status-counts", response_model=list[HostStatusCount])
async def get_status_counts(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = HostService(session)
    counts = await service.get_status_counts()
    return [HostStatusCount(status=s, count=c) for s, c in counts.items()]


@router.get("/{host_id}", response_model=HostPublic)
async def get_host(
    host_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = HostService(session)
    host = await service.get_by_id(host_id)
    return HostPublic.model_validate(host)


@router.post("/", response_model=HostPublic, status_code=status.HTTP_201_CREATED)
async def create_host(
    request: HostCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = HostService(session)
    host = await service.create(request)
    return HostPublic.model_validate(host)


@router.put("/{host_id}", response_model=HostPublic)
async def update_host(
    host_id: int,
    request: HostUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = HostService(session)
    host = await service.update(host_id, request)
    return HostPublic.model_validate(host)


@router.delete("/{host_id}", response_model=Message)
async def delete_host(
    host_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = HostService(session)
    await service.delete(host_id)
    return Message(detail="Host deleted successfully")


@router.post("/{host_id}/heartbeat", response_model=HostPublic)
async def heartbeat(
    host_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = HostService(session)
    host = await service.update_heartbeat(host_id)
    return HostPublic.model_validate(host)
