# Testing Guide

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=securesight --cov-report=term-missing

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
pytest tests/test_models.py
pytest tests/test_routes.py
pytest tests/test_services.py
pytest tests/test_ml.py

# Run with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "anomaly"
pytest -k "test_create_host"
```

## Test Architecture

```
tests/
├── conftest.py            # Shared fixtures and configuration
├── fixtures/
│   └── sample_data.json   # Test data files
├── unit/
│   └── test_placeholder.py
├── integration/
│   └── test_placeholder.py
├── e2e/
│   └── test_placeholder.py
├── test_models.py         # SQLAlchemy model tests
├── test_routes.py         # HTTP endpoint tests
├── test_services.py       # Service layer tests
└── test_ml.py             # ML detector tests
```

## Database Fixtures

Tests use a separate PostgreSQL database (`securesight_test`) that is created and destroyed per session. The `db_session` fixture provides a transactional scope that rolls back after each test.

## Writing Tests

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Model test
@pytest.mark.asyncio
async def test_create_host(db_session: AsyncSession):
    host = Host(hostname="test-host", ip_address="10.0.0.1")
    db_session.add(host)
    await db_session.flush()
    assert host.id is not None

# API test
@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```
