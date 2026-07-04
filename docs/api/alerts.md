# Alerts API

Endpoints for managing security alerts.

## `GET /api/v1/alerts/`

List alerts with optional filtering.

**Query Parameters:**

| Parameter  | Type   | Description                           |
|------------|--------|---------------------------------------|
| `status`   | string | Filter by status (new, acknowledged, resolved, dismissed) |
| `severity` | string | Filter by severity (info, warning, error, critical) |
| `host_id`  | int    | Filter by host                        |
| `skip`     | int    | Pagination offset (default: 0)        |
| `limit`    | int    | Page size (default: 100, max: 1000)   |

**Response:** `200 OK`
```json
{
  "items": [ { "id": 1, "title": "...", "severity": "critical", ... } ],
  "total": 42,
  "skip": 0,
  "limit": 100
}
```

## `POST /api/v1/alerts/`

Create a new alert.

**Request Body:**
```json
{
  "title": "Suspicious login from unknown IP",
  "description": "Failed login attempts from 10.0.0.1",
  "severity": "warning",
  "source_ip": "10.0.0.1",
  "host_id": 1
}
```

**Response:** `201 Created`

## `GET /api/v1/alerts/{id}`

Get alert details.

**Response:** `200 OK` with full alert object, or `404 Not Found`.

## `PATCH /api/v1/alerts/{id}`

Update alert status or assignment.

**Request Body:**
```json
{
  "status": "acknowledged",
  "assigned_to": 1
}
```

**Response:** `200 OK`

## `DELETE /api/v1/alerts/{id}`

Delete an alert.

**Response:** `204 No Content`
