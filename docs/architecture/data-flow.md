# Data Flow

This document describes how data flows through SecureSight.

## Metric Ingestion Flow

```
Host Agent ──POST /api/v1/metrics/──▶ API ──▶ PostgreSQL
                                          │
                                          └──▶ Redis Pub/Sub ──▶ Celery Task
                                                                    │
                                                            ┌───────▼────────┐
                                                            │ ML Detection   │
                                                            │ (Worker)       │
                                                            └───────┬────────┘
                                                                    │
                                              ┌─────────────────────┼──────────────┐
                                              ▼                     ▼              ▼
                                        Anomaly Event          Alert          Prometheus
                                        (PostgreSQL)        (PostgreSQL)      Metric
```

## Alert Lifecycle

1. **Ingestion** — Metrics arrive via API and are stored in PostgreSQL
2. **Detection** — Celery worker runs ML detectors (Isolation Forest, Z-Score, EMA)
3. **Evaluation** — Alert task evaluates detection results against active rules
4. **Creation** — If thresholds are exceeded, an Alert record is created
5. **Notification** — AlertManager routes the alert (email, Slack, PagerDuty)
6. **Response** — User acknowledges, investigates, and resolves the alert

## Authentication Flow

```
Client ──POST /auth/login──▶ API ──▶ Verify Password ──▶ JWT Issued
  │                                                          │
  │   ──Bearer Token in Authorization Header──▶              │
  │                                                          │
  └──▶ JWT Middleware ──▶ Verify Token ──▶ Extract User ──▶ Route Handler
```

## Batch Processing (Scheduled)

| Task                     | Schedule     | Description                        |
|--------------------------|-------------|-------------------------------------|
| `cleanup_old_alerts`     | Daily       | Remove resolved alerts > 90 days   |
| `purge_old_events`       | Daily       | Remove raw events > 30 days         |
| `run_anomaly_detection`  | Every 5 min | Run batch ML detection on recent metrics |
| `evaluate_alerts`        | Every 2 min | Evaluate metrics against rule thresholds |
