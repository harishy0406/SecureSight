"""Worker package for the SecureSight API.

Hosts the Celery application factory and the task modules that power the
asynchronous, scheduled, and maintenance work performed outside the request
lifecycle (anomaly scoring, alert dispatch, periodic retraining, housekeeping,
and similar background jobs).
"""

from __future__ import annotations

__all__: list[str] = []
