# Local Deployment

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Poetry or pip

## Setup

```bash
# Clone the repository
git clone https://github.com/your-org/securesight.git
cd securesight

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
alembic upgrade head

# Seed admin user
python scripts/seed_admin.py --email admin@securesight.local --password changeme

# Start the API server
uvicorn securesight.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Running Workers

```bash
# Start Celery worker (separate terminal)
celery -A securesight.api.workers.celery_app worker --loglevel=INFO

# Start Celery beat for scheduled tasks (separate terminal)
celery -A securesight.api.workers.celery_app beat --loglevel=INFO
```

## Docker Compose (Recommended)

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop all
docker compose down
```

Services will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093
- **Flower** (Celery UI): http://localhost:5555
