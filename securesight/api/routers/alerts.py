from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from securesight.api.core.database import get_session
from securesight.api.dependencies import get_current_user
from securesight.api.models.user import User
from securesight.api.schemas.alert import (
    AlertHistoryPublic,
    AlertRuleCreate,
    AlertRulePublic,
    AlertRuleUpdate,
)
from securesight.api.schemas.common import Message, PaginatedResponse
from securesight.api.services.alert_service import AlertService

router = APIRouter()


@router.get("/rules", response_model=PaginatedResponse[AlertRulePublic])
async def list_rules(
    page: int = 1,
    per_page: int = 50,
    enabled: bool | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = AlertService(session)
    rules, total = await service.get_rules(page=page, per_page=per_page, enabled=enabled)
    return PaginatedResponse(
        items=[AlertRulePublic.model_validate(r) for r in rules],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
    )


@router.get("/rules/{rule_id}", response_model=AlertRulePublic)
async def get_rule(
    rule_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = AlertService(session)
    rule = await service.get_rule_by_id(rule_id)
    return AlertRulePublic.model_validate(rule)


@router.post("/rules", response_model=AlertRulePublic, status_code=status.HTTP_201_CREATED)
async def create_rule(
    request: AlertRuleCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = AlertService(session)
    rule = await service.create_rule(request)
    return AlertRulePublic.model_validate(rule)


@router.put("/rules/{rule_id}", response_model=AlertRulePublic)
async def update_rule(
    rule_id: int,
    request: AlertRuleUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = AlertService(session)
    rule = await service.update_rule(rule_id, request)
    return AlertRulePublic.model_validate(rule)


@router.delete("/rules/{rule_id}", response_model=Message)
async def delete_rule(
    rule_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = AlertService(session)
    await service.delete_rule(rule_id)
    return Message(detail="Alert rule deleted")


@router.get("/history", response_model=PaginatedResponse[AlertHistoryPublic])
async def list_history(
    rule_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 50,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = AlertService(session)
    history, total = await service.get_history(rule_id=rule_id, status=status, page=page, per_page=per_page)
    return PaginatedResponse(
        items=[AlertHistoryPublic.model_validate(h) for h in history],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
    )


@router.post("/history/{alert_id}/resolve", response_model=AlertHistoryPublic)
async def resolve_alert(
    alert_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = AlertService(session)
    alert = await service.resolve_alert(alert_id)
    return AlertHistoryPublic.model_validate(alert)
