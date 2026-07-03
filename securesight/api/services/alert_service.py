from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select

from securesight.api.core.logging import get_logger
from securesight.api.models.alert_history import AlertHistory, AlertStatus
from securesight.api.models.alert_rule import AlertRule, AlertCondition, AlertSeverity
from securesight.api.services.base import BaseService

logger = get_logger(__name__)


class AlertService(BaseService):
    async def get_rules(
        self,
        page: int = 1,
        per_page: int = 50,
        enabled: bool | None = None,
    ) -> tuple[list[AlertRule], int]:
        query = select(AlertRule)
        if enabled is not None:
            query = query.where(AlertRule.enabled == enabled)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AlertRule.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_rule_by_id(self, rule_id: int) -> AlertRule:
        result = await self.session.execute(select(AlertRule).where(AlertRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if rule is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
        return rule

    async def create_rule(self, request) -> AlertRule:
        rule = AlertRule(**request.model_dump())
        return await self.commit_and_refresh(rule)

    async def update_rule(self, rule_id: int, request) -> AlertRule:
        rule = await self.get_rule_by_id(rule_id)
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)
        rule.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(rule)
        return rule

    async def delete_rule(self, rule_id: int) -> None:
        rule = await self.get_rule_by_id(rule_id)
        await self.session.delete(rule)
        await self.session.flush()

    async def evaluate_rule(self, rule: AlertRule, current_value: float) -> AlertHistory | None:
        now = datetime.now(timezone.utc)

        cooldown_result = await self.session.execute(
            select(AlertHistory).where(
                AlertHistory.alert_rule_id == rule.id,
                AlertHistory.status.in_([AlertStatus.FIRING, AlertStatus.ACKNOWLEDGED]),
            ).order_by(AlertHistory.fired_at.desc()).limit(1)
        )
        last_firing = cooldown_result.scalar_one_or_none()
        if last_firing:
            elapsed = (now - last_firing.fired_at).total_seconds()
            if elapsed < rule.cooldown_seconds:
                return None

        triggered = False
        if rule.condition == AlertCondition.GREATER_THAN:
            triggered = current_value > rule.threshold
        elif rule.condition == AlertCondition.LESS_THAN:
            triggered = current_value < rule.threshold
        elif rule.condition == AlertCondition.EQUAL_TO:
            triggered = current_value == rule.threshold
        elif rule.condition == AlertCondition.NOT_EQUAL:
            triggered = current_value != rule.threshold
        elif rule.condition == AlertCondition.OUTSIDE_RANGE and rule.threshold_high is not None:
            triggered = current_value < rule.threshold or current_value > rule.threshold_high
        elif rule.condition == AlertCondition.INSIDE_RANGE and rule.threshold_high is not None:
            triggered = rule.threshold <= current_value <= rule.threshold_high

        if not triggered:
            return None

        history = AlertHistory(
            alert_rule_id=rule.id,
            value=current_value,
            status=AlertStatus.FIRING,
            fired_at=now,
        )
        return await self.commit_and_refresh(history)

    async def get_history(
        self,
        rule_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[AlertHistory], int]:
        query = select(AlertHistory)
        if rule_id:
            query = query.where(AlertHistory.alert_rule_id == rule_id)
        if status:
            query = query.where(AlertHistory.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AlertHistory.fired_at.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def resolve_alert(self, alert_id: int) -> AlertHistory:
        result = await self.session.execute(select(AlertHistory).where(AlertHistory.id == alert_id))
        alert = result.scalar_one_or_none()
        if alert is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(alert)
        return alert
