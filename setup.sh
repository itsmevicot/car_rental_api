#!/usr/bin/env bash
set -euo pipefail

echo "Car Rental API - Setup"
echo "======================"
echo

if [ ! -f ".env" ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
fi

echo "Starting services with Docker Compose..."
docker compose up --build -d

echo
echo "Setup complete. Both services are starting."
echo "The API will be ready at http://localhost:8000/api/ in a few seconds."
echo "(Migrations and seed data are applied automatically by the container.)"
echo
echo "API:    http://localhost:8000/api/"
echo "Admin:  http://localhost:8000/admin/"
echo "Docs:   http://localhost:8000/api/docs/"
echo
echo "Run tests with:"
echo "  uv sync && uv run pytest"
