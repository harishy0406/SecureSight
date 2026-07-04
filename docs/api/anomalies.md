# Anomalies API

Endpoints for ML-detected anomalies.

## `GET /api/v1/anomalies/`

List anomalies.

**Query Parameters:**

| Parameter    | Type   | Description                             |
|-------------|--------|-----------------------------------------|
| `host_id`   | int    | Filter by host                          |
| `severity`  | string | Filter: low, medium, high, critical     |
| `status`    | string | Filter: pending, reviewed, dismissed     |
| `detector`  | string | Filter: isolation_forest, z_score, ema  |
| `skip`      | int    | Pagination offset                       |
| `limit`     | int    | Page size (default: 100)                |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "metric_name": "cpu_usage",
      "observed_value": 98.5,
      "anomaly_score": 0.95,
      "severity": "critical",
      "detector": "isolation_forest",
      "detected_at": "2026-06-15T10:30:00Z",
      "host_id": 1
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

## `GET /api/v1/anomalies/{id}`

Get anomaly details.

## `PATCH /api/v1/anomalies/{id}`

Review or update anomaly status.

```json
{
  "status": "reviewed",
  "notes": "False positive — legitimate batch job"
}
```

## `GET /api/v1/anomalies/stats`

Aggregated anomaly statistics.

**Response:**
```json
{
  "total_anomalies": 150,
  "by_severity": { "critical": 5, "high": 20, "medium": 50, "low": 75 },
  "top_detectors": ["isolation_forest", "z_score", "ema"],
  "recent_trend": "increasing"
}
```
