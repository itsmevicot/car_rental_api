#!/bin/bash
set -e

echo "🚗 API de Locação de Carros - Configuração do Docker"
echo "================================="
echo ""

# Run migrations
echo "📊 Executando migrations do banco de dados..."
python manage.py migrate --noinput

# Check if database is empty and load initial data
echo "📦 Verificando se os dados iniciais precisam ser carregados..."
if python manage.py shell -c "from rentals.models import Car; print(Car.objects.count())" | grep -q "^0$"; then
    echo "📥 Carregando dados de exemplo..."
    python manage.py shell < init_data.py
else
    echo "✓ Dados iniciais já existem"
fi

# Create superuser if it doesn't exist (optional)
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "👤 Criando superusuário..."
    python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Superusuário criado com sucesso')
else:
    print('Superusuário já existe')
EOF
fi

echo ""
echo "✅ Setup completo!"
echo "🚀 Iniciando servidor..."
echo ""

# Execute the main command
exec "$@"

