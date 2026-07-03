from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from securesight.api.models.anomaly_event import AnomalyEvent, AnomalySeverity, AnomalyStatus
from securesight.api.models.host import Host, HostStatus, HostType
from securesight.api.models.metric import Metric
from securesight.api.models.user import User, UserStatus


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    user = User(
        email="alice@example.com",
        username="alice",
        hashed_password="hashed_pw",
        display_name="Alice",
    )
    db_session.add(user)
    await db_session.flush()
    assert user.id is not None
    assert user.status == UserStatus.PENDING
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_create_host(db_session: AsyncSession):
    host = Host(
        hostname="web-01.example.com",
        ip_address="10.0.0.1",
        host_type=HostType.SERVER,
        cpu_cores=8,
        memory_total_mb=16384,
    )
    db_session.add(host)
    await db_session.flush()
    assert host.id is not None
    assert host.status == HostStatus.ONLINE


@pytest.mark.asyncio
async def test_create_metric(db_session: AsyncSession):
    host = Host(hostname="db-01", ip_address="10.0.0.2")
    db_session.add(host)
    await db_session.flush()

    metric = Metric(name="cpu_usage", value=75.5, unit="percent", host_id=host.id)
    db_session.add(metric)
    await db_session.flush()
    assert metric.id is not None
    assert metric.recorded_at is not None


@pytest.mark.asyncio
async def test_create_anomaly_event(db_session: AsyncSession):
    host = Host(hostname="anomaly-test")
    db_session.add(host)
    await db_session.flush()

    event = AnomalyEvent(
        metric_name="cpu_usage",
        observed_value=98.5,
        anomaly_score=0.95,
        severity=AnomalySeverity.CRITICAL,
        status=AnomalyStatus.PENDING,
        detector="isolation_forest",
        host_id=host.id,
    )
    db_session.add(event)
    await db_session.flush()
    assert event.id is not None
    assert event.detected_at is not None


@pytest.mark.asyncio
async def test_user_host_relationship(db_session: AsyncSession):
    user = User(email="bob@example.com", username="bob", hashed_password="pw")
    db_session.add(user)
    await db_session.flush()

    host = Host(hostname="bob-host", ip_address="10.0.0.3")
    db_session.add(host)
    await db_session.flush()

    result = await db_session.execute(select(Host).where(Host.hostname == "bob-host"))
    fetched = result.scalar_one()
    assert fetched.hostname == "bob-host"
