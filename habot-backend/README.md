# HABOT Backend

Docker-first Django backend using Neon PostgreSQL.

## Setup

1. Copy `.env.example` to `.env` and set a real Neon `DATABASE_URL` and Django `SECRET_KEY`.
2. Start the development environment:

   ```sh
   docker compose up --build
   ```

The backend is available at `http://localhost:8000`, Django Admin at `/admin/`, and readiness health at `/health/`.

Interactive OpenAPI documentation is available at `/api/docs/`; the OpenAPI schema is served at `/api/schema/`.

## API Contract

Current API version: `v1`.

All application endpoints are served under `/api/v1/...`. Authentication is intentionally
omitted for this hiring-project scope: mock Parent and LSA profiles are managed through
Django Admin, and clients select those mock records by ID.

Successful API responses use a consistent envelope:

```json
{
  "success": true,
  "message": "Booking created successfully.",
  "data": {}
}
```

Error responses use the matching error envelope:

```json
{
  "success": false,
  "message": "This slot is no longer available.",
  "errors": {}
}
```

Every response includes an `X-Request-ID` header. Clients may send their own
`X-Request-ID`; otherwise the API generates one and includes it in application logs.

Payment webhook processing is idempotent. Once a payment reaches a terminal state,
repeated terminal-state notifications return the current state without mutating the
transaction again.

## Health Checks

- `/health/live/` confirms the Django process is alive.
- `/health/ready/` checks the database connection with `SELECT 1`.
- `/health/` is kept as a readiness alias for Docker health checks.

## Commands

Run Django commands and tests inside Docker:

```sh
docker compose run --rm backend python manage.py createsuperuser
docker compose run --rm backend pytest
docker compose run --rm backend python manage.py check
```
