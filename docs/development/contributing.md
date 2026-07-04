# Contributing

## Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and write tests
4. Run the test suite: `pytest`
5. Run linting: `ruff check .`
6. Type-check: `mypy securesight/`
7. Commit using conventional commits
8. Push and open a Pull Request

## Code Style

- **Python**: Follow PEP 8, use `ruff` for linting and formatting
- **Type hints**: Required for all function signatures
- **Imports**: Grouped as stdlib → third-party → local, separated by blank lines
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants

## Commit Convention

```
<type>(<scope>): <description>

Types: feat, fix, refactor, test, docs, chore, style, perf, ci
Scope: api, ml, workers, docs, config, scripts
```

Examples:
- `feat(api): add alert dismissal endpoint`
- `fix(ml): handle empty window in EMA detector`
- `docs: add deployment guide for Kubernetes`

## Pull Request Process

1. Ensure tests pass and coverage does not decrease
2. Update documentation if adding/changing features
3. Add a changelog entry if relevant
4. Request review from at least one maintainer
5. Squash commits before merging

## Project Structure

```
securesight/
├── api/           # FastAPI application
│   ├── core/      # Config, database, dependencies
│   ├── models/    # SQLAlchemy ORM models
│   ├── routers/   # API route handlers
│   ├── schemas/   # Pydantic request/response schemas
│   ├── services/  # Business logic layer
│   └── workers/   # Celery background tasks
├── ml/            # ML detection engine
│   ├── detectors/ # Algorithm implementations
│   └── feature_engineering.py
├── prometheus/    # Prometheus configuration
├── alertmanager/  # AlertManager configuration
└── grafana/       # Grafana dashboards
```
