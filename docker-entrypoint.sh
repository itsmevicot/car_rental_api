#!/bin/bash
set -e

echo "Car Rental API - Docker Setup"
echo "============================="
echo ""

echo "Waiting for PostgreSQL..."
while ! uv run python -c "
import psycopg
try:
    psycopg.connect(
        host='${DB_HOST:-localhost}',
        port='${DB_PORT:-5432}',
        dbname='${DB_NAME:-car_rental}',
        user='${DB_USER:-car_rental}',
        password='${DB_PASSWORD:-car_rental}',
    )
    print('connected')
except Exception:
    exit(1)
" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is ready."

echo "Running migrations..."
if ! uv run python manage.py migrate --noinput 2>&1; then
    echo ""
    echo "ERROR: Migration failed. If you see 'InconsistentMigrationHistory',"
    echo "your database was created with a previous schema version."
    echo "Fix: docker compose down -v && docker compose up --build"
    echo ""
    exit 1
fi

echo "Checking initial data..."
if uv run python manage.py shell -c "from cars.models import Car; print(Car.objects.count())" | grep -q "^0$"; then
    echo "Loading seed data..."
    uv run python manage.py shell < init_data.py
else
    echo "Initial data already exists."
fi

if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Creating superuser..."
    uv run python manage.py createsuperuser --noinput 2>/dev/null || echo "Superuser already exists."
fi

echo ""
echo "Setup complete. Starting server..."
echo ""

exec "$@"
