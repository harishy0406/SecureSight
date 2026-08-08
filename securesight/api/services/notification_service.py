from __future__ import annotations

import json

from fastapi import HTTPException, status
from sqlalchemy import func, select

from securesight.api.core.logging import get_logger
from securesight.api.models.notification_channel import ChannelType, NotificationChannel
from securesight.api.services.base import BaseService
from securesight.api.workers.notification_tasks import dispatch_notification

logger = get_logger(__name__)


class NotificationService(BaseService):
    async def get_channels(
        self,
        page: int = 1,
        per_page: int = 50,
        channel_type: str | None = None,
    ) -> tuple[list[NotificationChannel], int]:
        query = select(NotificationChannel)
        if channel_type:
            query = query.where(NotificationChannel.channel_type == channel_type)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(NotificationChannel.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def create_channel(self, request) -> NotificationChannel:
        channel = NotificationChannel(**request.model_dump())
        return await self.commit_and_refresh(channel)

    async def update_channel(self, channel_id: int, request) -> NotificationChannel:
        result = await self.session.execute(select(NotificationChannel).where(NotificationChannel.id == channel_id))
        channel = result.scalar_one_or_none()
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification channel not found")
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(channel, field, value)
        await self.session.flush()
        await self.session.refresh(channel)
        return channel

    async def delete_channel(self, channel_id: int) -> None:
        result = await self.session.execute(select(NotificationChannel).where(NotificationChannel.id == channel_id))
        channel = result.scalar_one_or_none()
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification channel not found")
        await self.session.delete(channel)
        await self.session.flush()

    async def send_notification(self, channel: NotificationChannel, message: str, metadata: dict | None = None) -> None:
        destination = ""
        config = channel.config or {}
        if channel.channel_type == ChannelType.EMAIL:
            destination = config.get("email", "")
        elif channel.channel_type in (ChannelType.SLACK, ChannelType.WEBHOOK):
            destination = config.get("webhook_url", "")
        elif channel.channel_type == ChannelType.TELEGRAM:
            destination = config.get("chat_id", "")
            
        dispatch_notification.delay(
            channel_type=channel.channel_type.value,
            destination=destination,
            message=message,
            metadata=metadata or {}
        )
        logger.info("notification.dispatched", channel_id=channel.id, channel_type=channel.channel_type)
