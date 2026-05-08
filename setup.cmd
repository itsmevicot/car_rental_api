@echo off
setlocal enabledelayedexpansion

echo Car Rental API - Local Setup
echo ============================
echo.

where uv >nul 2>nul
if errorlevel 1 (
    echo Error: uv is required but was not found in PATH.
    echo Install guide: https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

if not exist ".env" (
    echo Creating .env from .env.example...
    copy /Y .env.example .env >nul
)

echo Loading environment variables from .env...
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "key=%%A"
    set "value=%%B"
    if defined key (
        if not "!key:~0,1!"=="#" if not "!key!"=="" set "!key!=!value!"
    )
)

echo Installing dependencies with uv...
uv sync
if errorlevel 1 exit /b 1

echo Starting PostgreSQL container...
docker compose up -d db
if errorlevel 1 exit /b 1

echo Running migrations...
uv run python manage.py migrate
if errorlevel 1 exit /b 1

echo Checking seed data...
for /f %%C in ('uv run python manage.py shell -c "from cars.models import Car; print(Car.objects.count())"') do set CAR_COUNT=%%C
if "%CAR_COUNT%"=="0" (
    echo Loading seed data...
    uv run python manage.py shell ^< init_data.py
) else (
    echo Seed data already present.
)

echo.
echo Setup complete.
echo.
echo Start the API with:
echo   uv run python manage.py runserver
echo.
echo Run tests with:
echo   uv run pytest
echo.
echo API:   http://localhost:8000/api/
echo Admin: http://localhost:8000/admin/
