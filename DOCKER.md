# Docker Setup

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

The stack starts:

- `db`: PostgreSQL
- `web`: Django API

## Environment

Docker Compose reads values from `.env`.

Important variables:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `API_PORT`
- `POSTGRES_HOST_PORT`
- `DOCKER_DB_HOST`

For local development outside Docker, the application uses `DB_HOST=localhost`.
Inside Docker, the web service overrides that value with `DOCKER_DB_HOST=db`.

## Entrypoint Behavior

The Docker entrypoint automatically:

- waits for PostgreSQL
- runs migrations
- loads seed data when the car catalog is empty
- optionally creates a Django superuser when the corresponding environment
  variables are set

## Useful Commands

```bash
docker compose up --build
docker compose up -d
docker compose up -d db
docker compose down
docker compose down -v
docker compose logs -f web
docker compose exec web uv run python manage.py shell
docker compose exec web uv run pytest
```

## Useful URLs

- API: `http://localhost:8000/api/`
- Admin: `http://localhost:8000/admin/`
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- OpenAPI schema: `http://localhost:8000/api/schema/`

## Notes

- seed data is loaded only when the fleet is empty
- PostgreSQL data is persisted in the `postgres_data` volume
- if you need a completely fresh environment, run `docker compose down -v`
