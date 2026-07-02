"""Structured logging configuration for the SecureSight API.

Wires :mod:`structlog` into the standard :mod:`logging` package so every
record, whether emitted by SecureSight code or by a third-party library, flows
through a single :class:`structlog.stdlib.ProcessorFormatter` pipeline.

The module also owns a dedicated :class:`contextvars.ContextVar` for the
request id so that the value survives even when the structlog context is
explicitly cleared (e.g. between background tasks).
"""

from __future__ import annotations

import contextvars
import logging
import sys
import uuid
from typing import Any

import structlog
from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
    merge_contextvars,
    unbind_contextvars,
)
from structlog.dev import ConsoleRenderer
from structlog.processors import (
    JSONRenderer,
    StackInfoRenderer,
    TimeStamper,
    add_log_level,
    format_exc_info,
)
from structlog.stdlib import (
    LoggerFactory,
    ProcessorFormatter,
)
from structlog import make_filtering_bound_logger

from securesight.api.core.config import Settings, get_settings

__all__ = [
    "bind_context",
    "clear_context",
    "configure_logging",
    "get_logger",
    "get_request_id",
    "new_request_id",
    "reset_request_id",
    "set_request_id",
    "unbind_context",
]

_LOG_LEVELS: dict[str, int] = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


_NOISY_LOGGERS: tuple[str, ...] = (
    "uvicorn.access",
    "uvicorn.error",
    "sqlalchemy.engine",
    "httpx",
    "httpcore",
    "celery.beat",
)

_REQUEST_ID_VAR: contextvars.ContextVar[str] = contextvars.ContextVar(
    "securesight_request_id",
    default="-",
)

_configured: bool = False


def _resolve_log_level(settings: Settings) -> int:
    raw = getattr(settings, "log_level", "INFO")
    if isinstance(raw, int):
        return raw
    return _LOG_LEVELS.get(str(raw).upper(), logging.INFO)


    if getattr(settings, "is_production", False):
        return True
    return bool(getattr(settings, "log_json", False))


def _add_request_id(
    _logger: Any,
    _method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    value = _REQUEST_ID_VAR.get()
    if value != "-":
        event_dict.setdefault("request_id", value)
    return event_dict


def _build_shared_processors(settings: Settings) -> list[Any]:
    processors: list[Any] = [
        merge_contextvars,
        add_log_level,
        TimeStamper(fmt="iso", utc=True),
        StackInfoRenderer(),
        format_exc_info,
    ]
    if bool(getattr(settings, "log_include_request_id", True)):
        processors.insert(1, _add_request_id)
    return processors


def _build_renderer(settings: Settings) -> Any:
    if _resolve_json(settings):
        return JSONRenderer()
    return ConsoleRenderer(colors=sys.stderr.isatty())


def configure_logging(settings: Settings | None = None) -> None:
    global _configured
    if _configured:
        return

    if settings is None:
        settings = get_settings()

    level = _resolve_log_level(settings)
    shared_processors = _build_shared_processors(settings)
    renderer = _build_renderer(settings)

    structlog.configure(
        processors=[
            *shared_processors,
            ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    handler.setLevel(level)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    for noisy_name in _NOISY_LOGGERS:
        noisy_logger = logging.getLogger(noisy_name)
        noisy_logger.setLevel(level)
        noisy_logger.propagate = True

    _configured = True


def get_logger(name: str | None = None) -> Any:
    logger = structlog.get_logger(name) if name else structlog.get_logger()
    return logger


def bind_context(**kwargs: Any) -> None:
    filtered = {key: value for key, value in kwargs.items() if value is not None}
    if filtered:
        bind_contextvars(**filtered)


def unbind_context(*keys: str) -> None:
    if keys:
        unbind_contextvars(*keys)


def clear_context() -> None:
    clear_contextvars()


def new_request_id() -> str:
    return uuid.uuid4().hex


def get_request_id() -> str:
    return _REQUEST_ID_VAR.get()


def set_request_id(request_id: str | None = None) -> contextvars.Token[str]:
    value = request_id if request_id is not None else new_request_id()
    return _REQUEST_ID_VAR.set(value)


def reset_request_id(token: contextvars.Token[str]) -> None:
    try:
        _REQUEST_ID_VAR.reset(token)
    except (ValueError, LookupError):
        pass
