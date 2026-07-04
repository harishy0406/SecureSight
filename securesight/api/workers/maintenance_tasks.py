from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from securesight.api.workers.celery_app import app as celery_app
from securesight.api.core.database import get_session_factory, dispose_engine
from securesight.api.core.logging import get_logger
from securesight.api.models.alert_history import AlertHistory, AlertStatus
from securesight.api.models.host import Host, HostStatus
from securesight.api.models.metric import Metric

logger = get_logger(__name__)


@celery_app.task(name="maintenance_tasks.cleanup_old_metrics")
def cleanup_old_metrics(retention_days: int = 30) -> str:
    import asyncio

    return asyncio.run(_cleanup_old_metrics(retention_days))


async def _cleanup_old_metrics(retention_days: int) -> str:
    async with get_session_factory()() as session:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        result = await session.execute(
            select(Metric).where(Metric.recorded_at < cutoff)
        )
        stale = result.scalars().all()
        count = len(stale)
        for metric in stale:
            await session.delete(metric)
        await session.commit()
        return f"Cleaned up {count} metrics older than {retention_days} days"


@celery_app.task(name="maintenance_tasks.cleanup_old_alerts")
def cleanup_old_alerts(retention_days: int = 90) -> str:
    import asyncio

    return asyncio.run(_cleanup_old_alerts(retention_days))


async def _cleanup_old_alerts(retention_days: int) -> str:
    async with get_session_factory()() as session:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        result = await session.execute(
            select(AlertHistory).where(
                AlertHistory.status == AlertStatus.RESOLVED,
                AlertHistory.resolved_at < cutoff,
            )
        )
        stale = result.scalars().all()
        count = len(stale)
        for alert in stale:
            await session.delete(alert)
        await session.commit()
        return f"Cleaned up {count} resolved alerts older than {retention_days} days"


@celery_app.task(name="maintenance_tasks.check_host_heartbeats")
def check_host_heartbeats(timeout_minutes: int = 5) -> str:
    import asyncio

    return asyncio.run(_check_host_heartbeats(timeout_minutes))


async def _check_host_heartbeats(timeout_minutes: int) -> str:
    async with get_session_factory()() as session:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
        result = await session.execute(
            select(Host).where(
                Host.last_seen_at < cutoff,
                Host.status == HostStatus.ONLINE,
            )
        )
        stale_hosts = result.scalars().all()
        for host in stale_hosts:
            host.status = HostStatus.OFFLINE
        await session.commit()
        return f"Marked {len(stale_hosts)} hosts as offline"
