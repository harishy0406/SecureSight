from __future__ import annotations

from typing import Any

from celery import Celery
from celery.signals import worker_process_init

from securesight.api.core.config import get_settings, reset_settings_cache
from securesight.api.core.logging import configure_logging, get_logger


_DEFAULT_BROKER_URL = "redis://localhost:6379/1"
_DEFAULT_RESULT_BACKEND = "redis://localhost:6379/2"
_DEFAULT_TASK_SERIALIZER = "json"
_DEFAULT_RESULT_SERIALIZER = "json"
_DEFAULT_TIMEZONE = "UTC"

_INCLUDE_MODULES: tuple[str, ...] = (
    "securesight.api.workers.alert_tasks",
    "securesight.api.workers.anomaly_tasks",
    "securesight.api.workers.maintenance_tasks",
)

_logger = get_logger("securesight.workers")


def _create_celery_app() -> Celery:
    settings = get_settings()
    broker_url = getattr(settings, "celery_broker_url", _DEFAULT_BROKER_URL)
    result_backend = getattr(settings, "celery_result_backend", _DEFAULT_RESULT_BACKEND)
    task_serializer = getattr(settings, "celery_task_serializer", _DEFAULT_TASK_SERIALIZER)
    result_serializer = getattr(
        settings, "celery_result_serializer", _DEFAULT_RESULT_SERIALIZER
    )
    timezone = getattr(settings, "celery_timezone", _DEFAULT_TIMEZONE)
    task_always_eager = bool(getattr(settings, "celery_task_always_eager", False))

    app = Celery(
        "securesight",
        broker=broker_url,
        backend=result_backend,
        include=list(_INCLUDE_MODULES),
    )

    app.conf.update(
        task_serializer=task_serializer,
        result_serializer=result_serializer,
        accept_content=["json"],
        timezone=timezone,
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        task_acks_on_failure_or_timeout=True,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        worker_send_task_events=True,
        task_send_sent_event=True,
        task_always_eager=task_always_eager,
        task_eager_propagates=task_always_eager,
        broker_connection_retry_on_startup=True,
        broker_connection_retry_max_retries=10,
    )

    return app


@worker_process_init.connect
def _on_worker_process_init(sender: Any, **kwargs: Any) -> None:
    reset_settings_cache()
    settings = get_settings()
    configure_logging(settings=settings)
    _logger.info(
        "celery.worker.process.init",
        broker_url=getattr(settings, "celery_broker_url", _DEFAULT_BROKER_URL),
        timezone=getattr(settings, "celery_timezone", _DEFAULT_TIMEZONE),
    )


app: Celery = _create_celery_app()


def run_worker() -> None:
    settings = get_settings()
    configure_logging(settings=settings)
    app.worker_main(["worker", "--loglevel=INFO"])


def run_beat() -> None:
    settings = get_settings()
    configure_logging(settings=settings)
    app.worker_main(["beat", "--loglevel=INFO"])


__all__ = ["app", "run_worker", "run_beat"]
