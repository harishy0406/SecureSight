from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def commit_and_refresh(self, instance: Any) -> Any:
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
