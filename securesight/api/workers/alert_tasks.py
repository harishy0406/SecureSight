from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select

from securesight.api.core.celery_app import celery_app
from securesight.api.core.database import async_session_factory
from securesight.api.core.logging import get_logger
from securesight.api.core.redis_client import get_redis_pool
from securesight.api.models.alert_history import AlertHistory, AlertStatus
from securesight.api.models.alert_rule import AlertRule
from securesight.api.models.metric import Metric

logger = get_logger(__name__)


@celery_app.task(name="alert_tasks.evaluate_alert_rules")
def evaluate_alert_rules() -> str:
    import asyncio

    return asyncio.run(_evaluate_alert_rules())


async def _evaluate_alert_rules() -> str:
    async with async_session_factory() as session:
        result = await session.execute(select(AlertRule).where(AlertRule.enabled == True))
        rules = result.scalars().all()

        triggered_count = 0
        for rule in rules:
            metric_result = await session.execute(
                select(Metric)
                .where(Metric.name == rule.metric_name)
                .order_by(Metric.recorded_at.desc())
                .limit(1)
            )
            latest_metric = metric_result.scalar_one_or_none()
            if latest_metric is None:
                continue

            triggered = False
            if rule.condition == "greater_than":
                triggered = latest_metric.value > rule.threshold
            elif rule.condition == "less_than":
                triggered = latest_metric.value < rule.threshold
            elif rule.condition == "equal_to":
                triggered = latest_metric.value == rule.threshold
            elif rule.condition == "outside_range" and rule.threshold_high is not None:
                triggered = latest_metric.value < rule.threshold or latest_metric.value > rule.threshold_high
            elif rule.condition == "inside_range" and rule.threshold_high is not None:
                triggered = rule.threshold <= latest_metric.value <= rule.threshold_high

            if not triggered:
                continue

            cooldown_result = await session.execute(
                select(AlertHistory).where(
                    AlertHistory.alert_rule_id == rule.id,
                    AlertHistory.status.in_([AlertStatus.FIRING, AlertStatus.ACKNOWLEDGED]),
                ).order_by(AlertHistory.fired_at.desc()).limit(1)
            )
            last = cooldown_result.scalar_one_or_none()
            if last:
                elapsed = (datetime.now(timezone.utc) - last.fired_at).total_seconds()
                if elapsed < rule.cooldown_seconds:
                    continue

            alert = AlertHistory(
                alert_rule_id=rule.id,
                value=latest_metric.value,
                status=AlertStatus.FIRING,
                fired_at=datetime.now(timezone.utc),
            )
            session.add(alert)
            await session.flush()

            redis = await get_redis_pool()
            await redis.publish("alerts", json.dumps({
                "type": "alert.fired",
                "rule_id": rule.id,
                "rule_name": rule.name,
                "metric_name": rule.metric_name,
                "value": latest_metric.value,
                "threshold": rule.threshold,
                "severity": rule.severity,
                "alert_id": alert.id,
            }))
            triggered_count += 1

        await session.commit()
        return f"Evaluated {len(rules)} rules, triggered {triggered_count} alerts"


@celery_app.task(name="alert_tasks.auto_resolve_alerts")
def auto_resolve_alerts() -> str:
    import asyncio

    return asyncio.run(_auto_resolve_alerts())


async def _auto_resolve_alerts() -> str:
    async with async_session_factory() as session:
        result = await session.execute(
            select(AlertHistory).where(
                AlertHistory.status == AlertStatus.FIRING,
            )
        )
        active_alerts = result.scalars().all()
        resolve_count = 0

        for alert in active_alerts:
            rule_result = await session.execute(select(AlertRule).where(AlertRule.id == alert.alert_rule_id))
            rule = rule_result.scalar_one_or_none()
            if rule is None:
                continue

            metric_result = await session.execute(
                select(Metric)
                .where(Metric.name == rule.metric_name)
                .order_by(Metric.recorded_at.desc())
                .limit(1)
            )
            latest = metric_result.scalar_one_or_none()
            if latest is None:
                continue

            still_triggered = False
            if rule.condition == "greater_than":
                still_triggered = latest.value > rule.threshold
            elif rule.condition == "less_than":
                still_triggered = latest.value < rule.threshold

            if not still_triggered:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now(timezone.utc)
                resolve_count += 1

        await session.commit()
        return f"Auto-resolved {resolve_count} alerts"
