# Architecture Overview

SecureSight is a security observability platform that collects, analyzes, and alerts on host and network telemetry using ML-based anomaly detection.

## High-Level Architecture

```
┌─────────────┐   ┌──────────────┐   ┌───────────────┐
│  Agents     │   │  API Server  │   │  ML Engine    │
│  (Hosts)    │──▶│  (FastAPI)   │──▶│  (Detectors)  │
└─────────────┘   └──────┬───────┘   └───────┬───────┘
                         │                   │
                         ▼                   ▼
                  ┌──────────────┐   ┌───────────────┐
                  │  PostgreSQL  │   │    Redis      │
                  │  (Metadata)  │   │  (Cache/Q)    │
                  └──────────────┘   └───────┬───────┘
                                             │
                                     ┌───────▼───────┐
                                     │    Celery     │
                                     │  (Workers)    │
                                     └───────┬───────┘
                                             │
                                     ┌───────▼───────┐
                                     │  Prometheus   │
                                     │  (Metrics)    │
                                     └───────┬───────┘
                                             │
                                     ┌───────▼───────┐
                                     │   Grafana     │
                                     │ (Dashboards)  │
                                     └───────────────┘
```

## Key Components

### API Server (FastAPI)
REST API for all platform operations — authentication, CRUD for hosts/alerts, metric ingestion. Uses async SQLAlchemy 2.0 with PostgreSQL. JWT-based auth.

### ML Engine
Three detection algorithms:
- **Isolation Forest** — unsupervised anomaly detection for multivariate patterns
- **Z-Score** — statistical outlier detection for threshold-based alerts
- **Exponential Moving Average (EMA)** — time-series trend deviation detection

### Celery Workers
Background task processing for:
- Alert evaluation and enrichment
- Anomaly detection runs
- Scheduled maintenance (data retention, cleanup)

### Monitoring Stack
- **Prometheus** — metrics collection and alerting rules
- **AlertManager** — alert routing (email, Slack, PagerDuty)
- **Grafana** — visualization dashboards

## Technology Stack

| Layer        | Technology                      |
|-------------|---------------------------------|
| Framework   | FastAPI (Python 3.11+)          |
| Database    | PostgreSQL 15 + asyncpg         |
| Cache/Queue | Redis 7                         |
| Task Queue  | Celery                          |
| ML          | scikit-learn, NumPy             |
| Monitoring  | Prometheus + Grafana            |
| Container   | Docker + Docker Compose         |
