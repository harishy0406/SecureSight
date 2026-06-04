# =============================================================================
# SecureSight — Makefile
# Run `make help` for a list of targets.
# =============================================================================

.PHONY: help install install-prod run run-prod worker beat flower \
        test test-unit test-integration test-cov lint format typecheck \
        migrate makemigration migrate-down seed seed-demo \
        build push helm-lint helm-install helm-install-prod helm-upgrade helm-uninstall \
        backup restore health up down logs ps restart clean clean-models

PYTHON        ?= python3
PIP           ?= $(PYTHON) -m pip
DOCKER        ?= docker
COMPOSE       ?= $(COMPOSE_CMD)
COMPOSE_CMD   ?= docker compose
HELM          ?= helm
KUBECTL       ?= kubectl
ALEMBIC       ?= $(PYTHON) -m alembic

IMAGE         ?= securesight/api
TAG           ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo latest)

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ============================== Install =====================================
install:  ## Install runtime + dev dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

install-prod:  ## Install runtime dependencies only
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# ================================ Run ======================================
run:  ## Run API (development, auto-reload)
	$(PYTHON) -m uvicorn securesight.api.main:app --reload --host 0.0.0.0 --port 8000

run-prod:  ## Run API (production, multi-worker)
	$(PYTHON) -m uvicorn securesight.api.main:app --host 0.0.0.0 --port 8000 --workers 4

worker:  ## Run Celery worker
	$(PYTHON) -m celery -A securesight.api.workers.celery_app worker --loglevel=INFO

beat:  ## Run Celery beat scheduler
	$(PYTHON) -m celery -A securesight.api.workers.celery_app beat --loglevel=INFO

flower:  ## Run Celery flower UI (port 5555)
	$(PYTHON) -m celery -A securesight.api.workers.celery_app flower --port=5555

# ================================ Test =====================================
test:  ## Run all tests
	$(PYTHON) -m pytest

test-unit:  ## Run unit tests only
	$(PYTHON) -m pytest -m unit

test-integration:  ## Run integration tests
	$(PYTHON) -m pytest -m integration

test-cov:  ## Run tests with HTML coverage report
	$(PYTHON) -m pytest --cov=securesight --cov-report=html --cov-report=term-missing

# ============================== Quality =====================================
lint:  ## Run ruff linter
	$(PYTHON) -m ruff check securesight tests scripts

format:  ## Format code (black + isort + ruff fix)
	$(PYTHON) -m black securesight tests scripts
	$(PYTHON) -m isort securesight tests scripts
	$(PYTHON) -m ruff check --fix securesight tests scripts

typecheck:  ## Run mypy
	$(PYTHON) -m mypy securesight

# ============================ Database ======================================
migrate:  ## Apply pending Alembic migrations
	$(ALEMBIC) upgrade head

makemigration:  ## Create new migration (set msg="description")
	$(ALEMBIC) revision --autogenerate -m "$(msg)"

migrate-down:  ## Rollback last migration
	$(ALEMBIC) downgrade -1

# ============================== Seed ========================================
seed:  ## Seed default admin user
	$(PYTHON) -m scripts.seed_admin

seed-demo:  ## Seed demo hosts, rules, dashboards
	$(PYTHON) -m scripts.seed_demo_data

# ============================= Docker =======================================
build:  ## Build Docker image
	$(DOCKER) build -t $(IMAGE):$(TAG) -t $(IMAGE):latest .

push: build  ## Push Docker image to registry
	$(DOCKER) push $(IMAGE):$(TAG)
	$(DOCKER) push $(IMAGE):latest

# ============================== Helm ========================================
helm-lint:  ## Lint Helm chart
	$(HELM) lint securesight/k8s/helm

helm-install:  ## Install Helm chart (dev values)
	$(HELM) install securesight securesight/k8s/helm \
		--namespace securesight --create-namespace \
		-f securesight/k8s/helm/values.dev.yaml

helm-install-prod:  ## Install Helm chart (prod values)
	$(HELM) install securesight securesight/k8s/helm \
		--namespace securesight --create-namespace \
		-f securesight/k8s/helm/values.prod.yaml

helm-upgrade:  ## Upgrade existing release
	$(HELM) upgrade securesight securesight/k8s/helm \
		--namespace securesight \
		-f securesight/k8s/helm/values.prod.yaml

helm-uninstall:  ## Uninstall Helm release
	$(HELM) uninstall securesight --namespace securesight

# ============================ Scripts =======================================
backup:  ## Backup database
	bash scripts/backup_db.sh

restore:  ## Restore database (set FILE=path/to/backup)
	bash scripts/restore_db.sh $(FILE)

health:  ## Run health check
	bash scripts/health_check.sh

# ====================== Docker Compose ======================================
up:  ## Start all services via docker compose
	$(COMPOSE) up -d

down:  ## Stop all services
	$(COMPOSE) down

logs:  ## Tail logs from all services
	$(COMPOSE) logs -f

ps:  ## List running services
	$(COMPOSE) ps

restart:  ## Restart all services
	$(COMPOSE) restart

# =========================== Maintenance ====================================
clean:  ## Remove caches and build artifacts
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -prune -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -prune -exec rm -rf {} +
	find . -type d -name '.ruff_cache' -prune -exec rm -rf {} +
	rm -rf build/ dist/ *.egg-info .coverage htmlcov/ coverage.xml

clean-models:  ## Remove trained ML model artifacts
	rm -f securesight/ml/models/*.pkl securesight/ml/models/*.joblib
