# Authentication API

Endpoints for user registration, login, and token management.

## `POST /api/v1/auth/register`

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "jdoe",
  "password": "SecurePass123!",
  "display_name": "Jane Doe"
}
```

**Response:** `201 Created`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": { "id": 1, "email": "user@example.com", "username": "jdoe" }
}
```

## `POST /api/v1/auth/login`

Authenticate and receive access token.

**Request Body:**
```json
{
  "username": "jdoe",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK` (same format as register), or `401 Unauthorized`.

## `POST /api/v1/auth/refresh`

Refresh an expiring token. Requires valid bearer token.

**Response:** `200 OK` with new token.

## `POST /api/v1/auth/logout`

Invalidate current session token.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

## `GET /api/v1/auth/me`

Get current authenticated user profile.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "jdoe",
  "display_name": "Jane Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2026-01-01T00:00:00Z"
}
```
