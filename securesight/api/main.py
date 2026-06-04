from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import structlog
import uvicorn
from fastapi import APIRouter, FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from securesight.api.core.config import Settings, get_settings
from securesight.api.core.database import dispose_engine, ping_database
from securesight.api.core.logging import configure_logging
from securesight.api.core.middleware import install_middleware
from securesight.api.core.redis_client import close_redis, ping_redis

logger = structlog.get_logger("securesight.api.main")


async def _safe(label: str, coro: Any) -> Any:
    try:
        return await coro
    except Exception as exc:
        logger.error(
            "securesight.api.background_task_failed",
            task=label,
            exc_type=type(exc).__name__,
        )
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    configure_logging(settings)
    log = logger.bind(
        app_name=getattr(settings, "app_name", "SecureSight"),
        version=getattr(settings, "app_version", "1.0.0"),
        environment=getattr(settings, "app_env", "development"),
        debug=getattr(settings, "debug", False),
    )
    log.info("securesight.api.startup.begin")
    app.state.started_at = datetime.now(timezone.utc)

    db_ok = False
    redis_ok = False

    db_result = await _safe("database.ping", ping_database())
    if isinstance(db_result, dict):
        db_ok = bool(db_result.get("ok", db_result.get("healthy", False)))

    redis_result = await _safe("redis.ping", ping_redis())
    if isinstance(redis_result, dict):
        redis_ok = bool(redis_result.get("ok", redis_result.get("healthy", False)))

    app.state.db_ready = db_ok
    app.state.redis_ready = redis_ok

    log.info(
        "securesight.api.startup.complete",
        database=db_ok,
        redis=redis_ok,
    )

    try:
        yield
    finally:
        log.info("securesight.api.shutdown.begin")
        await _safe("database.dispose", dispose_engine())
        await _safe("redis.close", close_redis())
        log.info("securesight.api.shutdown.complete")


def _install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        logger.warning(
            "securesight.api.http_exception",
            status_code=exc.status_code,
            detail=str(exc.detail),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "status_code": exc.status_code},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.error(
            "securesight.api.unhandled_exception",
            exc_type=type(exc).__name__,
            exc_message=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "status_code": 500},
        )


def _install_routes(app: FastAPI, settings: Settings) -> None:
    app_name = getattr(settings, "app_name", "SecureSight")
    app_version = getattr(settings, "app_version", "1.0.0")
    app_env = getattr(settings, "app_env", "development")

    health = APIRouter(tags=["health"])

    @health.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "service": app_name}

    @health.get("/ready")
    async def readiness() -> JSONResponse:
        db_ok = bool(getattr(app.state, "db_ready", False))
        redis_ok = bool(getattr(app.state, "redis_ready", False))
        ready = db_ok and redis_ok
        body = {
            "status": "ready" if ready else "not_ready",
            "database": db_ok,
            "redis": redis_ok,
            "service": app_name,
            "version": app_version,
        }
        return JSONResponse(
            status_code=200 if ready else 503,
            content=body,
        )

    @health.get("/version")
    async def version_info() -> dict[str, str]:
        return {
            "service": app_name,
            "version": app_version,
            "environment": app_env,
        }

    app.include_router(health)

    api_v1 = APIRouter(prefix="/api/v1", tags=["v1"])

    @api_v1.get("/ping")
    async def ping() -> dict[str, str]:
        return {"message": "pong", "api": "v1"}

    app.include_router(api_v1)


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = get_settings()

    app_name = getattr(settings, "app_name", "SecureSight")
    app_version = getattr(settings, "app_version", "1.0.0")
    description = f"{app_name} — security and observability platform API."
    docs_enabled = bool(getattr(settings, "docs_enabled", True))

    app = FastAPI(
        title=app_name,
        version=app_version,
        description=description,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.state.db_ready = False
    app.state.redis_ready = False
    app.state.started_at = None

    install_middleware(app, settings)
    _install_exception_handlers(app)
    _install_routes(app, settings)

    logger.debug(
        "securesight.api.app_built",
        app_name=app_name,
        app_version=app_version,
        docs_enabled=docs_enabled,
    )
    return app


app: FastAPI = create_app()


def run() -> None:
    settings = get_settings()
    configure_logging(settings)
    host = getattr(settings, "api_host", "0.0.0.0")
    port = int(getattr(settings, "api_port", 8000))
    workers = int(getattr(settings, "api_workers", 1))
    reload = bool(getattr(settings, "api_reload", False))
    logger.info(
        "securesight.api.serving",
        host=host,
        port=port,
        workers=workers,
        reload=reload,
    )
    uvicorn.run(
        "securesight.api.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=1 if reload else workers,
        log_config=None,
        access_log=False,
    )


if __name__ == "__main__":
    run()
