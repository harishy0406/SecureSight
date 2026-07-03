from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from securesight.api.core.celery_app import celery_app
from securesight.api.core.database import async_session_factory
from securesight.api.core.logging import get_logger
from securesight.api.core.redis_client import get_redis_pool
from securesight.api.models.anomaly_event import AnomalyEvent, AnomalySeverity, AnomalyStatus
from securesight.api.models.host import Host
from securesight.api.models.metric import Metric
from securesight.ml.pipeline import run_anomaly_detection

logger = get_logger(__name__)


@celery_app.task(name="anomaly_tasks.run_detection")
def run_detection(host_id: int | None = None) -> str:
    import asyncio

    return asyncio.run(_run_detection(host_id))


async def _run_detection(host_id: int | None = None) -> str:
    async with async_session_factory() as session:
        query = select(Metric).order_by(Metric.recorded_at.desc()).limit(1000)
        if host_id:
            query = query.where(Metric.host_id == host_id)
        result = await session.execute(query)
        metrics = result.scalars().all()

        if not metrics:
            return "No metrics to analyze"

        records = [
            {
                "id": m.id,
                "name": m.name,
                "value": m.value,
                "host_id": m.host_id,
                "recorded_at": m.recorded_at.isoformat(),
            }
            for m in metrics
        ]

        detections = run_anomaly_detection(records)
        created_count = 0

        for det in detections:
            event = AnomalyEvent(
                metric_name=det["metric_name"],
                observed_value=det["observed_value"],
                predicted_value=det.get("predicted_value"),
                anomaly_score=det["anomaly_score"],
                severity=det.get("severity", AnomalySeverity.MEDIUM),
                status=AnomalyStatus.PENDING,
                detector=det["detector"],
                explanation=det.get("explanation"),
                context=det.get("context"),
                host_id=det["host_id"],
            )
            session.add(event)
            created_count += 1

        await session.flush()
        redis = await get_redis_pool()
        await redis.publish("anomalies", json.dumps({
            "type": "anomaly.detection_complete",
            "host_id": host_id,
            "detected_count": created_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))

        await session.commit()
        return f"Analyzed {len(metrics)} metrics, detected {created_count} anomalies"


@celery_app.task(name="anomaly_tasks.cleanup_old_anomalies")
def cleanup_old_anomalies(retention_days: int = 90) -> str:
    import asyncio

    return asyncio.run(_cleanup_old_anomalies(retention_days))


async def _cleanup_old_anomalies(retention_days: int) -> str:
    async with async_session_factory() as session:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        result = await session.execute(
            select(AnomalyEvent).where(AnomalyEvent.created_at < cutoff)
        )
        stale = result.scalars().all()
        count = len(stale)
        for event in stale:
            await session.delete(event)
        await session.commit()
        return f"Cleaned up {count} anomaly events older than {retention_days} days"
