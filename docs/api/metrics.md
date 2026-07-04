# Metrics API

Endpoints for host metrics and telemetry data.

## `GET /api/v1/metrics/`

List metrics with optional filtering.

**Query Parameters:**

| Parameter  | Type   | Description                          |
|-----------|--------|--------------------------------------|
| `host_id`  | int    | Filter by host                       |
| `name`     | string | Filter by metric name (e.g., cpu_usage) |
| `from`     | string | ISO-8601 start time                  |
| `to`       | string | ISO-8601 end time                    |
| `skip`     | int    | Pagination offset                    |
| `limit`    | int    | Page size (default: 100)            |

## `POST /api/v1/metrics/`

Submit host metrics.

**Request Body:**
```json
{
  "host_id": 1,
  "name": "cpu_usage",
  "value": 75.5,
  "unit": "percent",
  "labels": { "core": "0" }
}
```

## `GET /api/v1/metrics/series`

Time-series aggregated data for charting.

**Query Parameters:**

| Parameter  | Type   | Description                          |
|-----------|--------|--------------------------------------|
| `host_id`  | int    | Required                             |
| `name`     | string | Required                             |
| `window`   | string | Aggregation window: 1m, 5m, 1h, 1d  |
| `from`     | string | ISO-8601 start                       |
| `to`       | string | ISO-8601 end                         |

**Response:**
```json
{
  "host_id": 1,
  "metric": "cpu_usage",
  "window": "5m",
  "points": [
    { "timestamp": "2026-06-15T10:00:00Z", "avg": 45.2, "max": 78.1, "min": 22.3 },
    { "timestamp": "2026-06-15T10:05:00Z", "avg": 52.1, "max": 81.0, "min": 30.5 }
  ]
}
```
