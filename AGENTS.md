# AGENTS

This document defines the engineering rules for contributors and coding agents
working in this repository.

## Purpose

Use this file as the default contract for code changes. When a tradeoff is
needed, prefer consistency with these rules over local convenience.

## Stack and Tooling

- Python `3.12`
- Django `4.2`
- Django REST Framework
- PostgreSQL
- `uv` for dependency and command execution
- `ruff` for linting and formatting
- `ty` for static typing checks
- `pytest` for tests
- `pytest-cov` for coverage
- `structlog` for structured logs
- `drf-spectacular` for OpenAPI, Swagger UI, and ReDoc

## Required Commands

Run all project commands through `uv`.

Examples:

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
uv run ruff check .
uv run ruff format .
uv run ty check .
uv run pytest
uv run pytest --cov=core --cov=cars --cov=customers --cov=rentals --cov=rewards --cov-report=term-missing
```

## Quality Gates

Every change must keep the repository green.

- `ruff check .` must pass
- `ruff format` output must be clean
- `ty check .` must pass
- the full `pytest` suite must pass
- total coverage must remain at `100%`

Do not merge work that weakens these guarantees.

## Architecture Rules

The codebase follows a layered structure.

### Models

- Models define persistence structure and model-level invariants.
- Do not place orchestration logic in models.
- Keep models small and predictable.

### Repositories

- Repositories are the only place where ORM queries are executed.
- Use repositories for lookups, filtering, locking, aggregation, and persistence
  access patterns.
- Direct use of `.objects`, `select_for_update`, `get_object_or_404`, or raw ORM
  queries outside repositories is not allowed.

### Services

- Services own business rules and application orchestration.
- Pricing, reward calculation, authorization decisions at the domain layer,
  visibility rules, and workflow coordination belong in services.
- Services may call repositories, other services, constants, and domain
  exceptions.
- Services must not build HTTP responses.

### Views

- Views are HTTP adapters.
- Views may read request data, invoke serializers, call services, and shape the
  HTTP response envelope.
- Views must not contain ORM queries.
- Views must not contain core business rules.
- Keep conditional logic in views limited to request and response concerns.

### Serializers

- Serializers validate transport input and shape transport output.
- Do not move business rules into serializers unless the rule is purely about
  request payload validation.

## API Design Rules

- Keep response envelopes consistent.
- Reuse the centralized error format from the custom exception handler.
- Prefer explicit authorization behavior over silent fallback.
- Public and staff visibility rules must be consistent across list and detail
  endpoints.
- Query parameters must be validated explicitly when the endpoint supports a
  constrained set of values.

## Documentation Rules

### General Docstrings

- Write docstrings in English.
- Use Google Style docstrings for non-trivial functions, classes, and methods.
- Document `Args`, `Returns`, and `Raises` when they are relevant.

### View Docstrings

View docstrings are part of the public API documentation because they appear in
`/api/docs` and `/api/redoc`.

For views:

- describe the endpoint from the API consumer perspective
- explain what the endpoint returns
- mention authentication or staff restrictions when relevant
- mention important visibility or filtering rules when relevant
- avoid internal implementation language such as `queryset`, `serializer`, or
  schema-generation details unless unavoidable
- keep the text concise and useful in Swagger/ReDoc

## Logging Rules

Critical operations must be observable.

- Log the start of important workflows
- Log successful completion of important workflows
- Log failures with enough structured context to debug
- Use structured logging fields instead of burying context in free text

Critical flows include at least:

- rental creation
- rental return
- reward earning
- reward redemption
- request-level HTTP logging

## Concurrency Rules

- Protect mutation flows that can race with row-level locking when appropriate.
- Use repository methods to encapsulate `select_for_update`.
- Keep locking narrow and purposeful.
- Do not spread locking logic across views or serializers.

## Typing Rules

- New production code must be fully typed.
- Prefer precise types over `Any` or `object`.
- Type repository returns, service interfaces, serializer helpers, and view
  method signatures where practical.
- Tests do not need the same level of strictness as production code, but should
  still be typed when straightforward.

## Testing Rules

- Every change must include tests when behavior changes.
- Add tests in the app that owns the behavior.
- Keep test fixtures scoped to each app under `app/tests/conftest.py`.
- Shared object builders may live in `app/tests/support.py`.
- Prefer meaningful scenario coverage over redundant implementation-detail tests.

Minimum expectation for behavior changes:

- happy path coverage
- authorization coverage where relevant
- validation and error coverage where relevant
- regression coverage for the exact behavior being changed

## Pagination and List Endpoint Rules

- Endpoints returning multiple objects should be paginated unless there is a
  deliberate and documented exception.
- Public list endpoints must behave consistently with their detail endpoints.
- Export endpoints such as CSV or PDF may intentionally bypass pagination when
  the endpoint contract requires a full export.

## Admin Rules

- Historical ledger-like data must be read-only in Django admin.
- Admin editing must not bypass domain guarantees for immutable records.

## Migration and Data Rules

- Never edit committed migrations retroactively.
- Add new migrations for schema changes.
- Preserve existing data contracts unless the change explicitly requires a
  versioned or coordinated migration.

## Change Discipline

- Make the smallest change that correctly solves the problem.
- Do not introduce parallel patterns for the same concern.
- Refactor toward existing conventions instead of adding new local styles.
- Preserve endpoint compatibility unless a contract change is intentional and
  documented.

## Git and Safety Rules

- Do not perform destructive git operations.
- Do not revert user work without explicit instruction.
- Do not rewrite history unless explicitly requested.

## When in Doubt

If a situation is ambiguous, prefer:

1. repository-centered data access
2. service-centered business rules
3. thin views
4. explicit tests
5. stricter typing
6. clearer public API documentation
