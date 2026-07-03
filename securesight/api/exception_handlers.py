from __future__ import annotations

import logging
from typing import Any

import orjson
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from securesight.api.core.logging import get_logger, get_request_id

logger = get_logger(__name__)


def _build_error_response(
    detail: str,
    status_code: int,
    request_id: str | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"detail": detail}
    if request_id:
        body["request_id"] = request_id
    if errors:
        body["errors"] = errors
    return JSONResponse(content=body, status_code=status_code)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _build_error_response(
        detail=str(exc.detail),
        status_code=exc.status_code,
        request_id=get_request_id(),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {
            "field": ".".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg", "Validation error"),
            "type": err.get("type", ""),
        }
        for err in exc.errors()
    ]
    return _build_error_response(
        detail="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        request_id=get_request_id(),
        errors=errors,
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.error("database.integrity_error", error=str(exc))
    return _build_error_response(
        detail="Resource conflict or constraint violation",
        status_code=status.HTTP_409_CONFLICT,
        request_id=get_request_id(),
    )


async def operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
    logger.error("database.operational_error", error=str(exc))
    return _build_error_response(
        detail="Database operation failed",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        request_id=get_request_id(),
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error("database.error", error=str(exc))
    return _build_error_response(
        detail="A database error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=get_request_id(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled.exception", error=str(exc), error_type=type(exc).__name__)
    return _build_error_response(
        detail="Internal server error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=get_request_id(),
    )


def install_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(IntegrityError, integrity_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(OperationalError, operational_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]
