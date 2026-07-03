from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from securesight.api.core.config import get_settings
from securesight.api.models.host import Host
from securesight.api.schemas.host import HostCreate
from securesight.api.services.host_service import HostService


@pytest.mark.asyncio
async def test_create_host_service(db_session: AsyncSession):
    service = HostService(db_session)
    request = HostCreate(hostname="service-test", ip_address="10.0.0.10", cpu_cores=4)
    host = await service.create(request)
    assert host.hostname == "service-test"
    assert host.cpu_cores == 4


@pytest.mark.asyncio
async def test_get_host_not_found(db_session: AsyncSession):
    service = HostService(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.get_by_id(99999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_hostname(db_session: AsyncSession):
    service = HostService(db_session)
    request = HostCreate(hostname="dup-test")
    await service.create(request)
    with pytest.raises(HTTPException) as exc:
        await service.create(request)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_heartbeat(db_session: AsyncSession):
    host = Host(hostname="hb-test", status="online")
    db_session.add(host)
    await db_session.flush()

    service = HostService(db_session)
    updated = await service.update_heartbeat(host.id)
    assert updated.last_seen_at is not None
