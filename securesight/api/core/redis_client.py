"""Async Redis client, cache helpers, and pub/sub for SecureSight.

Provides a lazily-initialised connection pool, JSON-backed cache helpers,
and channel constants for anomaly, alert, and notification events.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import orjson
import redis.asyncio as redis_async
from redis.asyncio.client import PubSub
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError

from securesight.api.core.config import get_settings

CHANNEL_ANOMALIES = "securesight:anomalies"
CHANNEL_ALERTS = "securesight:alerts"
CHANNEL_NOTIFICATIONS = "securesight:notifications"

ANOMALIES_CHANNEL = CHANNEL_ANOMALIES
ALERTS_CHANNEL = CHANNEL_ALERTS
NOTIFICATIONS_CHANNEL = CHANNEL_NOTIFICATIONS

_LOGGER = logging.getLogger("securesight.redis")

_pool: ConnectionPool | None = None
_client: redis_async.Redis | None = None


def _resolve_url() -> str:
    settings = get_settings()
    return getattr(settings, "redis_url", "redis://localhost:6379/0")


def _pool_kwargs() -> dict[str, Any]:
    settings = get_settings()
    return {
        "max_connections": getattr(settings, "max_connections", 50),
        "socket_timeout": getattr(settings, "socket_timeout", 5.0),
    }


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            _resolve_url(),
            decode_responses=False,
            **_pool_kwargs(),
        )
    return _pool


def get_redis() -> redis_async.Redis:
    global _client
    if _client is None:
        _client = redis_async.Redis(connection_pool=get_pool())
    return _client


def reset_redis() -> None:
    global _pool, _client
    _pool = None
    _client = None


async def close_redis() -> None:
    global _pool, _client
    if _client is not None:
        try:
            await _client.aclose()
        except RedisError as exc:
            _LOGGER.warning("redis client close failed: %s", exc.__class__.__name__)
        _client = None
    if _pool is not None:
        try:
            await _pool.aclose()
        except (RedisError, OSError) as exc:
            _LOGGER.warning("redis pool close failed: %s", exc.__class__.__name__)
        _pool = None


async def ping_redis(timeout: float = 5.0) -> dict[str, Any]:
    client = get_redis()
    try:
        async with asyncio.timeout(timeout):
            pong = await client.ping()
        return {"ok": bool(pong), "error": None}
    except (RedisError, OSError, TimeoutError) as exc:
        _LOGGER.warning("redis ping failed: %s", exc.__class__.__name__)
        return {"ok": False, "error": str(exc)}


def _serialize(value: Any) -> bytes:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("utf-8")
    return orjson.dumps(value, default=str)


def _deserialize(value: bytes | None) -> Any:
    if value is None:
        return None
    try:
        return orjson.loads(value)
    except orjson.JSONDecodeError:
        return value


async def cache_set(
    key: str,
    value: Any,
    ttl_seconds: int | None = None,
) -> bool:
    if not key:
        return False
    client = get_redis()
    payload = _serialize(value)
    try:
        if ttl_seconds is not None and ttl_seconds > 0:
            return bool(await client.set(key, payload, ex=ttl_seconds))
        return bool(await client.set(key, payload))
    except RedisError as exc:
        _LOGGER.warning("redis cache_set failed: %s", exc.__class__.__name__)
        return False


async def cache_get(key: str) -> Any:
    if not key:
        return None
    client = get_redis()
    try:
        raw = await client.get(key)
    except RedisError as exc:
        _LOGGER.warning("redis cache_get failed: %s", exc.__class__.__name__)
        return None
    return _deserialize(raw)


async def cache_delete(*keys: str) -> int:
    if not keys:
        return 0
    client = get_redis()
    try:
        return int(await client.delete(*keys))
    except RedisError as exc:
        _LOGGER.warning("redis cache_delete failed: %s", exc.__class__.__name__)
        return 0


async def publish(channel: str, message: Any) -> int:
    if not channel:
        return 0
    client = get_redis()
    try:
        return int(await client.publish(channel, _serialize(message)))
    except RedisError as exc:
        _LOGGER.warning("redis publish failed: %s", exc.__class__.__name__)
        return 0


async def publish_anomaly(message: Any) -> int:
    return await publish(CHANNEL_ANOMALIES, message)


async def publish_alert(message: Any) -> int:
    return await publish(CHANNEL_ALERTS, message)


async def publish_notification(message: Any) -> int:
    return await publish(CHANNEL_NOTIFICATIONS, message)


@asynccontextmanager
async def subscribe(*channels: str) -> AsyncIterator[PubSub]:
    if not channels:
        raise ValueError("at least one channel is required")
    client = get_redis()
    pubsub = client.pubsub(ignore_subscribe_messages=True)
    try:
        await pubsub.subscribe(*channels)
        yield pubsub
    finally:
        try:
            await pubsub.unsubscribe(*channels)
        except RedisError:
            pass
        try:
            await pubsub.aclose()
        except RedisError:
            pass


__all__ = [
    "CHANNEL_ANOMALIES",
    "CHANNEL_ALERTS",
    "CHANNEL_NOTIFICATIONS",
    "ANOMALIES_CHANNEL",
    "ALERTS_CHANNEL",
    "NOTIFICATIONS_CHANNEL",
    "get_pool",
    "get_redis",
    "reset_redis",
    "close_redis",
    "ping_redis",
    "cache_set",
    "cache_get",
    "cache_delete",
    "publish",
    "publish_anomaly",
    "publish_alert",
    "publish_notification",
    "subscribe",
]
