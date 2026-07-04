# Development Setup

## System Requirements

- Python 3.11 or later
- PostgreSQL 15
- Redis 7
- Git
- Docker & Docker Compose (optional but recommended)

## Quick Start (Docker)

```bash
git clone https://github.com/your-org/securesight.git
cd securesight

# Copy environment configuration
cp .env.example .env

# Start all services
docker compose up -d

# Run database migrations
docker compose exec api alembic upgrade head

# Seed admin user
docker compose exec api python scripts/seed_admin.py

# Check logs
docker compose logs -f api
```

## Manual Setup

### 1. Python Environment

```bash
# Using poetry (recommended)
poetry install
poetry shell

# Or using pip + venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database

```bash
# Create database
createdb securesight

# Run migrations
alembic upgrade head

# Seed admin user
python scripts/seed_admin.py --email admin@securesight.local --password changeme
```

### 3. Run

```bash
# Terminal 1: API server
uvicorn securesight.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Celery worker
celery -A securesight.api.workers.celery_app worker --loglevel=INFO

# Terminal 3: Celery beat
celery -A securesight.api.workers.celery_app beat --loglevel=INFO
```

## Environment Variables

| Variable              | Default                   | Description                   |
|----------------------|---------------------------|-------------------------------|
| `APP_ENV`            | `development`             | Environment name              |
| `APP_DEBUG`          | `true`                    | Debug mode                    |
| `DATABASE_URL`       | `postgresql+asyncpg://...`| Async database URL            |
| `REDIS_URL`          | `redis://localhost:6379/0`| Redis connection              |
| `CELERY_BROKER_URL`  | `redis://localhost:6379/1`| Celery broker                 |
| `SECRET_KEY`         | (auto-generated)          | JWT signing key               |
| `LOG_LEVEL`          | `DEBUG`                   | Logging level                 |

## Verify Setup

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Should return: {"status": "healthy", "version": "1.0.0"}
```
