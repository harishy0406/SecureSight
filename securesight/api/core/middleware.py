from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Literal

import orjson
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp

from securesight.api.core.config import Settings, get_settings
from securesight.api.core.logging import (
    bind_context,
    clear_context,
    get_logger,
    reset_request_id,
    set_request_id,
)
from securesight.api.core.redis_client import get_redis

logger = get_logger(__name__)
stdlib_logger = logging.getLogger("securesight.middleware")

__all__ = [
    "RequestContextMiddleware",
    "RateLimitMiddleware",
    "RateLimitMiddlewareRedis",
    "SecurityHeadersMiddleware",
    "install_middleware",
]


_RATE_LIMIT_EXCLUDED: frozenset[str] = frozenset(
    {
        "/health",
        "/ready",
        "/version",
        "/metrics",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    }
)


_DEFAULT_PERMISSIONS_POLICY: str = (
    "geolocation=(), microphone=(), camera=(), payment=()"
)


def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    if request.client is not None:
        return request.client.host
    return "unknown"


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id") or set_request_id()
        client_ip = _get_client_ip(request)
        bind_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
        )
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            logger.error(
                "request.failed",
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            logger.info(
                "request.completed",
                status=status_code,
                duration_ms=round(duration_ms, 2),
            )
            clear_context()
            reset_request_id()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, is_production: bool = False) -> None:
        super().__init__(app)
        self._is_production = bool(is_production)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )
        response.headers.setdefault(
            "Permissions-Policy",
            _DEFAULT_PERMISSIONS_POLICY,
        )
        if self._is_production:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        per_minute: int = 60,
        burst: int = 20,
    ) -> None:
        super().__init__(app)
        self._per_minute: int = max(1, int(per_minute))
        self._burst: int = max(0, int(burst))
        self._capacity: int = self._per_minute + self._burst
        self._window_seconds: float = 60.0
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, timestamps: deque[float], window_start: float) -> None:
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in _RATE_LIMIT_EXCLUDED:
            return await call_next(request)
        client_ip = _get_client_ip(request)
        now = time.monotonic()
        window_start = now - self._window_seconds
        timestamps = self._requests[client_ip]
        self._prune(timestamps, window_start)
        if len(timestamps) >= self._capacity:
            oldest = timestamps[0] if timestamps else now
            retry_after = max(1, int(self._window_seconds - (now - oldest)) + 1)
            stdlib_logger.warning(
                "rate_limit_exceeded client_ip=%s path=%s",
                client_ip,
                request.url.path,
            )
            logger.warning(
                "rate_limit.exceeded",
                backend="memory",
                client_ip=client_ip,
                path=request.url.path,
            )
            return _too_many_requests(retry_after)
        timestamps.append(now)
        return await call_next(request)


class RateLimitMiddlewareRedis(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        per_minute: int = 60,
        burst: int = 20,
    ) -> None:
        super().__init__(app)
        self._per_minute: int = max(1, int(per_minute))
        self._burst: int = max(0, int(burst))
        self._capacity: int = self._per_minute + self._burst
        self._window_seconds: int = 60

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in _RATE_LIMIT_EXCLUDED:
            return await call_next(request)
        client_ip = _get_client_ip(request)
        bucket = int(time.time()) // self._window_seconds
        key = f"rl:{client_ip}:{bucket}"
        try:
            client = get_redis()
            pipe = client.pipeline()
            pipe.incr(key)
            pipe.expire(key, self._window_seconds * 2)
            results = await pipe.execute()
            count = int(results[0]) if results else 0
        except Exception as exc:  # noqa: BLE001
            stdlib_logger.warning(
                "rate_limit_redis_check_failed client_ip=%s err=%s",
                client_ip,
                exc,
            )
            logger.warning(
                "rate_limit.redis_unavailable",
                client_ip=client_ip,
                path=request.url.path,
                error=str(exc),
            )
            return await call_next(request)
        if count > self._capacity:
            stdlib_logger.warning(
                "rate_limit_exceeded client_ip=%s count=%s",
                client_ip,
                count,
            )
            logger.warning(
                "rate_limit.exceeded",
                backend="redis",
                client_ip=client_ip,
                path=request.url.path,
                count=count,
            )
            return _too_many_requests(self._window_seconds)
        return await call_next(request)


def _too_many_requests(retry_after: int) -> Response:
    body = orjson.dumps({"detail": "Too Many Requests"})
    return Response(
        content=body,
        status_code=429,
        media_type="application/json",
        headers={"Retry-After": str(max(1, int(retry_after)))},
    )


def _select_rate_limiter(settings: Settings) -> type[BaseHTTPMiddleware]:
    storage: Literal["memory", "redis"] = settings.rate_limit_storage
    if storage == "redis" and (settings.is_staging or settings.is_production):
        return RateLimitMiddlewareRedis
    return RateLimitMiddleware


def install_middleware(
    app: FastAPI,
    settings: Settings | None = None,
) -> None:
    cfg = settings or get_settings()

    app.add_middleware(
        SecurityHeadersMiddleware,
        is_production=cfg.is_production,
    )

    if cfg.rate_limit_enabled:
        limiter_cls = _select_rate_limiter(cfg)
        app.add_middleware(
            limiter_cls,
            per_minute=cfg.rate_limit_per_minute,
            burst=cfg.rate_limit_burst,
        )

    app.add_middleware(RequestContextMiddleware)

    if cfg.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(cfg.cors_origins),
            allow_methods=list(cfg.cors_allow_methods),
            allow_headers=list(cfg.cors_allow_headers),
            allow_credentials=cfg.cors_allow_credentials,
        )
