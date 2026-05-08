# Car Rental API

Car Rental API is a Django REST Framework project for managing a car rental
business with an integrated customer rewards system.

The project started from a simpler rental API and was expanded with:

- JWT authentication
- customer and staff access scoping
- reward summaries and transaction history
- point redemption with rental discounts
- loyalty tiers with multipliers
- Swagger UI, ReDoc, and OpenAPI schema
- a Postman collection with end-to-end, negative, and edge-case coverage

## Project Structure

The codebase is organized by domain:

- `cars/`: public fleet catalog
- `customers/`: authentication and customer records
- `rentals/`: rental creation, listing, detail, return, and stats
- `rewards/`: reward ledger, summaries, history, and redemption
- `core/`: shared infrastructure such as pagination, exception handling, and
  request logging

## Architecture

The project follows a layered approach:

- `views` handle HTTP concerns, serializers, and response formatting
- `services` own business rules and workflow orchestration
- `repositories` are the only place where ORM queries are executed
- `models` define persistence structure and model-level invariants

The rewards system is based on a ledger. Instead of storing a mutable reward
balance on the customer, the current balance is derived from
`RewardTransaction` history.

## AI Agent Instructions

The repository includes an `AGENTS.md` file with project-specific instructions
for AI coding agents and contributors acting through agent workflows.

That file documents the expected engineering rules for this codebase, including:

- architectural boundaries
- typing expectations
- documentation rules
- testing and validation requirements
- repository conventions

If the project conventions change, `AGENTS.md` should be updated as part of the
same change so that the written guidance stays aligned with the real codebase.

## Main Features

- public car catalog with consistent visibility rules for unavailable cars
- rental creation and return flow
- rental detail with customer-scoped visibility
- reward summary and history for authenticated customers
- cross-customer reward and rental views for staff users
- reward redemption with structured transaction breakdown
- CSV and PDF export for reward history

## Prerequisites

- Python `3.12+`
- `uv`
- Docker and Docker Compose

`uv` documentation:

- https://docs.astral.sh/uv/

## Environment Variables

The project uses a local `.env` file.

1. Copy `.env.example` to `.env`
2. Adjust values if needed

The setup scripts create `.env` automatically when it does not exist.

Important notes:

- local development uses `DB_HOST=localhost`
- Docker uses `DOCKER_DB_HOST=db`
- `docker-compose.yml` reads values from `.env`
- `.env` is intentionally ignored by Git

## Local Setup

### Option 1: Setup scripts

Linux/macOS:

```bash
./setup.sh
```

Windows (CMD):

```bat
setup.cmd
```

Windows (PowerShell):

```powershell
cmd /c setup.cmd
```

> **Note for Windows users**: `setup.cmd` is a CMD script and must be run
> from CMD or via `cmd /c setup.cmd` from PowerShell. Running it directly
> in a PowerShell terminal may produce unexpected behaviour.

What the scripts do:

- create `.env` from `.env.example` when needed
- start both the PostgreSQL and API services via Docker Compose
- migrations and seed data are applied automatically by the container on first boot

### Option 2: Manual setup

Linux/macOS / Git Bash:

```bash
cp .env.example .env
docker compose up --build -d
```

Windows CMD:

```bat
copy .env.example .env
docker compose up --build -d
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

API base URL:

```text
http://localhost:8000/api/
```

Admin URL:

```text
http://localhost:8000/admin/
```

## Docker Setup

```bash
cp .env.example .env
docker compose up --build
```

The Docker entrypoint automatically:

- waits for PostgreSQL
- runs migrations
- loads seed data when the fleet is empty
- optionally creates a superuser if the corresponding environment variables are set

Useful Docker URLs:

- API: `http://localhost:8000/api/`
- Admin: `http://localhost:8000/admin/`
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- OpenAPI schema: `http://localhost:8000/api/schema/`

## Seed Data

Seed data is loaded from `init_data.py`.

What is seeded:

- an initial fleet of cars across economic, standard, and premium pricing tiers

When it runs:

- automatically in Docker when the `cars` table is empty
- manually in local development through the setup scripts

## Authentication

The API uses JWT Bearer tokens.

Auth endpoints:

- `POST /api/auth/register/`
- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`
- `GET /api/auth/me/`

Use the access token as:

```text
Authorization: Bearer <token>
```

## API Documentation

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI schema: `/api/schema/`

View docstrings are written to be useful in Swagger and ReDoc because they are
part of the generated endpoint documentation.

## Core Endpoints

### Cars

- `GET /api/cars/`
- `GET /api/cars/{car_id}/`

### Rentals

- `POST /api/rentals/create/`
- `GET /api/rentals/`
- `GET /api/rentals/{rental_id}/`
- `POST /api/rentals/{rental_id}/return/`
- `GET /api/rentals/customer/{customer_email}/`
- `GET /api/rentals/customers/{customer_id}/`
- `GET /api/rentals/stats/`

### Rewards

- `GET /api/rewards/`
- `GET /api/rewards/history/`
- `GET /api/rewards/transactions/{transaction_id}/`
- `POST /api/rewards/apply/`
- `GET /api/rewards/customer/{customer_email}/`
- `GET /api/rewards/customer/{customer_email}/history/`
- `GET /api/rewards/customers/{customer_id}/`
- `GET /api/rewards/customers/{customer_id}/history/`

### Health

- `GET /api/health/`
- `GET /api/ready/`

## Postman Collection

The repository includes an updated Postman collection:

- `postman_collection.json`

How to use it:

1. Import the collection into Postman
2. Set `base_url` if needed
3. Set `admin_email` and `admin_password` in the collection or environment
4. Run the `Bootstrap` folder first
5. Then run the role-based folders and negative scenarios

The collection covers:

- public endpoints
- auth flows
- admin, bronze, silver, and gold scenarios
- `401`, `403`, `404`, validation failures, and business-rule errors
- rental detail visibility
- edge-case reward flows

## Running Tests

Quick run:

```bash
uv run pytest
```

Full run with coverage:

```bash
uv run --with pytest --with pytest-django --with pytest-cov python -m pytest --cov=core --cov=cars --cov=customers --cov=rentals --cov=rewards --cov-report=term-missing -q -s
```

## Validation Commands

These are the validation commands used in the repository.

Lint:

```bash
uv run --with ruff ruff check .
```

What it validates:

- import ordering
- unused imports
- common correctness issues
- style rules configured in `pyproject.toml`

Format:

```bash
uv run --with ruff ruff format --check .
```

What it validates:

- formatting consistency according to Ruff

Type checking:

```bash
uv run --with ty ty check .
```

What it validates:

- static type consistency for production code
- repository, service, serializer, and view interfaces

Tests with coverage:

```bash
uv run --with pytest --with pytest-django --with pytest-cov python -m pytest --cov=core --cov=cars --cov=customers --cov=rentals --cov=rewards --cov-report=term-missing -q -s
```

What it validates:

- behavior correctness
- regression coverage
- role-based access control
- edge cases and error scenarios
- total coverage gate of `100%`

Schema generation:

```bash
uv run python manage.py spectacular --file /tmp/schema.yaml
```

What it validates:

- OpenAPI schema generation
- documentation integrity for DRF endpoints

## Pre-push Hook

The repository includes a pre-push hook configuration through `pre-commit`.

Install it once:

```bash
uv run --with pre-commit pre-commit install --hook-type pre-push
```

## Additional Notes

- PostgreSQL is the default database
- `structlog` is used for structured HTTP and domain logs
- historical reward transactions are read-only in Django admin
- rental creation in Django admin uses the same domain service used by the API
