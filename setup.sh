#!/usr/bin/env bash
set -euo pipefail

echo "Car Rental API - Local Setup"
echo "============================"
echo

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is required but was not found in PATH."
  echo "Install guide: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

if [ ! -f ".env" ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
fi

echo "Loading environment variables from .env..."
set -a
. ./.env
set +a

echo "Installing dependencies with uv..."
uv sync

echo "Starting PostgreSQL container..."
docker compose up -d db

echo "Running migrations..."
uv run python manage.py migrate

echo "Checking seed data..."
if uv run python manage.py shell -c "from cars.models import Car; print(Car.objects.count())" | grep -q "^0$"; then
  echo "Loading seed data..."
  uv run python manage.py shell < init_data.py
else
  echo "Seed data already present."
fi

echo
echo "Setup complete."
echo
echo "Start the API with:"
echo "  set -a && source .env && set +a && uv run python manage.py runserver"
echo
echo "Run tests with:"
echo "  uv run pytest"
echo
echo "API:   http://localhost:8000/api/"
echo "Admin: http://localhost:8000/admin/"
