# SecureSight – AI-Powered Infrastructure Monitoring & Observability Platform
>**Transforming infrastructure telemetry into AI-driven insights for proactive operations.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Prometheus](https://img.shields.io/badge/Prometheus-Monitoring-red?logo=prometheus)](https://prometheus.io)
[![Grafana](https://img.shields.io/badge/Grafana-Visualization-orange?logo=grafana)](https://grafana.com)
[![Docker](https://img.shields.io/badge/Docker-Containerization-blue?logo=docker)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Orchestration-brightgreen?logo=kubernetes)](https://kubernetes.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?logo=postgresql)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-Caching-red?logo=redis)](https://redis.io)
[![AI/ML](https://img.shields.io/badge/AI-MachineLearning-orange)]()


## 🎯 Overview

SecureSight is a cloud-native Infrastructure Monitoring and Observability Platform designed to provide organizations with comprehensive visibility into the health, performance, and reliability of their distributed systems. Modern applications are increasingly deployed across multiple servers, containers, microservices, and cloud environments, making infrastructure monitoring a critical requirement for maintaining system stability and ensuring seamless user experiences. SecureSight addresses these challenges by delivering real-time monitoring, telemetry aggregation, anomaly detection, automated alerting, and centralized observability through an integrated platform.

The primary objective of SecureSight is to help DevOps teams, Site Reliability Engineers (SREs), system administrators, and infrastructure managers proactively identify performance bottlenecks, resource utilization issues, service outages, and abnormal system behaviors before they impact business operations. By combining metrics collection, analytics, visualization, and intelligent alerting into a unified solution, SecureSight enables organizations to achieve higher system availability, faster incident response, and improved operational efficiency.

## Highlights

- 📊 Real-time metrics collection from servers, VMs, containers, Kubernetes, databases, and network devices via Prometheus exporters
- 🤖 AI-powered anomaly detection using historical baselines, trend analysis, and outlier detection to predict issues before they escalate
- 📈 Rich visualizations with Grafana dashboards for CPU, memory, disk, network, latency, and custom business metrics
- 🚨 Automated alerting via email, Slack, Teams, Telegram, and webhooks with severity-based routing
- ☸️ Cloud-native deployment with Docker containerization and Kubernetes orchestration for scalability and resilience
- 🔐 Enterprise-grade security with JWT authentication, RBAC, API access control, and audit logging
- 💾 Hybrid storage: PostgreSQL for relational configuration data and Redis for real-time caching and fast metric retrieval
- ⚡ Performance optimizations including asynchronous FastAPI endpoints, database indexing, connection pooling, and horizontal scaling

## 🛠️ Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, FastAPI |
| Data Collection | Prometheus Exporters (node-exporter, blackbox-exporter, custom exporters) |
| Monitoring & Storage | Prometheus (time-series DB), PostgreSQL (metadata), Redis (caching) |
| Visualization | Grafana |
| AI/ML | scikit-learn, TensorFlow/PyTorch (for anomaly detection models) |
| Containerization | Docker |
| Orchestration | Kubernetes |
| Security | JWT, OAuth2, Role-Based Access Control (RBAC) |
| Frontend | HTML, CSS, JavaScript (Grafana panels) |
| Infrastructure | Linux/Windows servers, VMs, Docker, Kubernetes |

## 🏗️ Architecture

The SecureSight platform follows a microservices-based cloud-native architecture designed for scalability, reliability, and fault tolerance.
<p align="center">
<img width="1536" height="1024" alt="ChatGPT Image Jun 4, 2026, 09_10_50 AM" src="https://github.com/user-attachments/assets/9be3c633-5a32-4bfb-96cf-b04499fd806f" />
</p>

### Core Data Flow

1. **Data Collection Layer**: Prometheus exporters deployed on infrastructure components (servers, containers, Kubernetes, etc.) expose metrics such as CPU, memory, disk I/O, network throughput, and application-specific indicators.
2. **Monitoring and Metrics Layer**: Prometheus scrapes metrics from exporters at configurable intervals, stores time-series data, and manages metric labels and metadata.
3. **Backend Services Layer**: FastAPI-based backend processes incoming telemetry, aggregates metrics, manages alert configurations, handles authentication, and provides RESTful APIs for dashboard interactions. Asynchronous processing enables high-throughput handling of monitoring data.
4. **AI-Powered Anomaly Detection**: The anomaly detection engine analyzes historical metrics to build baseline models, detect trends, recognize seasonal patterns, and identify outliers that indicate potential issues.
5. **Data Storage Layer**: 
   - PostgreSQL stores user accounts, alert configurations, dashboard settings, infrastructure inventory, monitoring policies, and historical metadata.
   - Redis provides real-time caching, session management, fast metric retrieval, and temporary alert queues.
6. **Dashboard and Visualization**: Grafana dashboards visualize metrics with interactive charts, time-series graphs, and drill-down capabilities for rapid root-cause analysis.
7. **Automated Alerting System**: When anomalies or threshold breaches are detected, alerts are generated and routed via email, Slack, Teams, Telegram, or webhooks based on severity (Informational, Warning, Critical).
8. **Containerization and Orchestration**: All services are containerized using Docker and deployed on Kubernetes for automatic scaling, self-healing, load balancing, and high availability.

## 📂 Project Structure

```text
SecureSight/
├── app/
│   ├── __init__.py              # FastAPI app factory, middleware, router inclusion
│   ├── main.py                  # Application entrypoint
│   ├── core/
│   │   ├── config.py            # Application settings
│   │   ├── security.py          # Authentication, JWT, RBAC utilities
│   │   └── database.py          # Database connection, session management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── metrics.py       # Metrics ingestion and querying endpoints
│   │   │   ├── alerts.py        # Alert rule management and notification endpoints
│   │   │   ├── anomalies.py     # AI anomaly detection endpoints
│   │   │   └── health.py        # Health check endpoints
│   ├── services/
│   │   ├── prometheus.py        # Prometheus querying and metric aggregation
│   │   ├── anomaly_detector.py  # ML model for anomaly detection (isolation forest, LSTM autoencoder, etc.)
│   │   ├── alert_manager.py     # Alert rule evaluation and notification dispatch
│   │   └── kafka.py             # Optional event streaming integration
│   ├── models/
│   │   ├── user.py              # User account model
│   │   ├── alert.py             # Alert configuration and incident model
│   │   ├── infrastructure.py    # Infrastructure inventory model (hosts, services, etc.)
│   │   └── metric.py            # Metric metadata model
│   ├── utils/
│   │   ├── logging.py           # Structured logging configuration
│   │   └── helpers.py           # Utility functions
│   └── templates/               # HTML templates for any server-rendered pages (if needed)
├── docker/
│   ├── Dockerfile               # Multi-stage Docker build for FastAPI app
│   ├── prometheus/
│   │   └── prometheus.yml       # Prometheus server configuration
│   └── grafana/
│       ├── provisioning/
│       │   ├── dashboards/
│       │   └── datasources/
│       └── grafana.ini          # Grafana configuration
├── k8s/
│   ├── deployment.yaml          # Kubernetes deployments for backend, Prometheus, Grafana
│   ├── service.yaml             # Internal cluster services
│   ├── ingress.yaml             # External access (if applicable)
│   └── hpa.yaml                 # Horizontal Pod Autoscaler configurations
├── ml/
│   ├── models/                  # Trained anomaly detection model artifacts
│   ├── train.py                 # Model training script
│   └── evaluate.py              # Model evaluation script
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── conftest.py              # Pytest fixtures
├── scripts/
│   ├── setup.sh                 # Development environment setup
│   └── deploy.sh                # Deployment helper scripts
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Development dependencies (testing, linting)
├── README.md
└── .gitignore
```

## ⚡ Getting Started

### Prerequisites

- Python 3.10 or newer recommended
- pip
- Docker & Docker Compose (for containerized deployment)
- kubectl (for Kubernetes deployment)
- A modern browser (for accessing Grafana dashboards)

### Installation (Local Development)

1. Clone the repository and enter the project folder.

   ```bash
   git clone https://github.com/harishy0406/SecureSight
   cd SecureSight
   ```

2. Create and activate a virtual environment.

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

   On macOS/Linux:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies.

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (copy `.env.example` to `.env` and adjust).

   ```bash
   cp .env.example .env
   ```

   Key variables:
   - `SECRET_KEY`: JWT signing key
   - `DATABASE_URL`: PostgreSQL connection string
   - `REDIS_URL`: Redis connection string
   - `PROMETHEUS_URL`: Prometheus server URL
   - `GRAFANA_URL`: Grafana server URL

5. Initialize the database.

   ```bash
   python -m app.core.database init
   ```

6. Start the application.

   ```bash
   python -m app.main
   ```

   The API will be available at `http://localhost:8000`.

### Deployment with Docker Compose

1. Ensure Docker Compose is installed.
2. Build and start the services.

   ```bash
   docker-compose up -d
   ```

3. Access the services:
   - API: `http://localhost:8000`
   - Grafana: `http://localhost:3000` (admin/admin)
   - Prometheus: `http://localhost:9090`

### Default Admin Login

When the application starts, it creates a development admin account if one does not already exist.

```text
Email: admin@securesight.com
Password: admin123
```

Change these credentials before using the project outside local development.

## 📖 Usage

### Operator Workflow

1. Access the API documentation at `http://localhost:8000/docs` (Swagger UI).
2. Use the metrics endpoints to ingest infrastructure telemetry:
   - `POST /api/v1/metrics/` - Submit metric data points
   - `GET /api/v1/metrics/` - Query stored metrics with filtering
3. View anomaly detection results:
   - `GET /api/v1/anomalies/` - Retrieve detected anomalies
   - `POST /api/v1/anomalies/detect` - Trigger anomaly detection on recent data
4. Configure alert rules:
   - `POST /api/v1/alerts/` - Create new alert rules
   - `GET /api/v1/alerts/` - List active alert rules
5. View triggered alerts and incidents:
   - `GET /api/v1/alerts/incidents` - List alert incidents

### Admin Workflow

1. Log in to Grafana at `http://localhost:3000` with default credentials (admin/admin) or via OAuth if configured.
2. Import pre-built dashboards (available in `grafana/dashboards/`).
3. Configure data sources (Prometheus, PostgreSQL) if not already set up.
4. Create custom dashboards for specific infrastructure views.
5. Manage users and roles in Grafana (if using Grafana's auth) or via the API for application-level RBAC.
6. Monitor system health via the health check endpoint: `GET /api/v1/health`
7. Scale deployments using Kubernetes HPA or Docker Compose replica settings.

## 🔑 Key Pages and Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/` | GET | API root - service information |
| `/docs` | GET | Swagger UI API documentation |
| `/redoc` | GET | ReDoc API documentation |
| `/api/v1/metrics` | GET, POST | Ingest and query infrastructure metrics |
| `/api/v1/anomalies` | GET, POST | Retrieve anomalies, trigger detection |
| `/api/v1/alerts` | GET, POST | Manage alert rules and notifications |
| `/api/v1/alerts/incidents` | GET | List triggered alert incidents |
| `/api/v1/health` | GET | Service health check (liveness, readiness) |
| `/api/v1/infrastructure` | GET, POST | Manage infrastructure inventory (hosts, services) |
| `/api/v1/users` | GET, POST | User management (admin only) |
| `/api/v1/auth/login` | POST | User login (JWT token) |
| `/api/v1/auth/logout` | POST | User logout |
| `/api/v1/auth/refresh` | POST | Refresh JWT token |

## 📊 Data Models

| Model | Purpose |
| --- | --- |
| `User` | Accounts, roles, authentication tokens, and audit trails |
| `Metric` | Time-series metric data points with labels, timestamps, and values |
| `Anomaly` | Detected anomalies with score, timestamp, affected metric, and severity |
| `AlertRule` | Alert configurations including conditions, thresholds, and notification channels |
| `AlertIncident` | Triggered alerts with status, timestamps, and resolution information |
| `Infrastructure` | Inventory of monitored components (hosts, containers, services, etc.) |
| `InfrastructureMetric` | Aggregated metrics per infrastructure component for dashboarding |

## ⚙️ Configuration

Most runtime settings live in `app/core/config.py` and can be overridden via environment variables.

| Setting | Purpose | Environment Variable |
| --- | --- | --- |
| `SECRET_KEY` | JWT signing key for authentication | `SECRET_KEY` |
| `DATABASE_URL` | PostgreSQL connection string | `DATABASE_URL` |
| `REDIS_URL` | Redis connection string for caching | `REDIS_URL` |
| `PROMETHEUS_URL` | Prometheus server URL for querying | `PROMETHEUS_URL` |
| `GRAFANA_URL` | Grafana server URL for dashboard linking | `GRAFANA_URL` |
| `ALERT_CHECK_INTERVAL` | Seconds between alert rule evaluations | `ALERT_CHECK_INTERVAL` |
| `ANOMALY_DETECTION_INTERVAL` | Seconds between anomaly detection runs | `ANOMALY_DETECTION_INTERVAL` |
| `MODEL_PATH` | Filesystem path to trained anomaly detection model | `MODEL_PATH` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `LOG_LEVEL` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token expiration time | `ACCESS_TOKEN_EXPIRE_MINUTES` |
| `ALERT_EMAIL_SMTP_HOST` | SMTP host for email notifications | `ALERT_EMAIL_SMTP_HOST` |
| `ALERT_EMAIL_SMTP_PORT` | SMTP port for email notifications | `ALERT_EMAIL_SMTP_PORT` |
| `ALERT_EMAIL_SENDER` | Sender address for email alerts | `ALERT_EMAIL_SENDER` |
| `ALERT_SLACK_WEBHOOK_URL` | Slack webhook URL for alerts | `ALERT_SLACK_WEBHOOK_URL` |
| `ALERT_TEAMS_WEBHOOK_URL` | Microsoft Teams webhook URL for alerts | `ALERT_TEAMS_WEBHOOK_URL` |
| `ALERT_TELEGRAM_BOT_TOKEN` | Telegram bot token for alerts | `ALERT_TELEGRAM_BOT_TOKEN` |
| `ALERT_TELEGRAM_CHAT_ID` | Telegram chat ID for alerts | `ALERT_TELEGRAM_CHAT_ID` |

For production, prefer environment variables for sensitive values such as `SECRET_KEY`, `DATABASE_URL`, and notification credentials.

## 🤝 Contributing

Contributions are welcome. Please keep changes focused, test user-facing flows, and document any configuration or database changes.

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a pull request.

Please ensure your code follows the existing style and includes appropriate tests.

---

<div align="center">

**Made with ❤️ by M Harish Guatham**

⭐ If you find this project helpful, please star it! ⭐

</div>
