@echo off

echo Car Rental API - Setup
echo ======================
echo.

if not exist ".env" (
    echo Creating .env from .env.example...
    copy /Y .env.example .env >nul
)

echo Starting services with Docker Compose...
docker compose up --build -d
if errorlevel 1 exit /b 1

echo.
echo Setup complete. Both services are starting.
echo The API will be ready at http://localhost:8000/api/ in a few seconds.
echo (Migrations and seed data are applied automatically by the container.)
echo.
echo API:    http://localhost:8000/api/
echo Admin:  http://localhost:8000/admin/
echo Docs:   http://localhost:8000/api/docs/
echo.
echo Run tests with:
echo   uv sync ^&^& uv run pytest
