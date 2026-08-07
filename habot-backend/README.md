# HABOT Backend

Docker-first Django backend using Neon PostgreSQL.

## Setup

1. Copy `.env.example` to `.env` and set a real Neon `DATABASE_URL` and Django `SECRET_KEY`.
2. Start the development environment:

   ```sh
   docker compose up --build
   ```

The backend is available at `http://localhost:8000`, Django Admin at `/admin/`, and the health endpoint at `/health/`.

Interactive OpenAPI documentation is available at `/api/docs/`; the OpenAPI schema is served at `/api/schema/`.

## Commands

Run Django commands and tests inside Docker:

```sh
docker compose run --rm backend python manage.py createsuperuser
docker compose run --rm backend pytest
docker compose run --rm backend python manage.py check
```
