#!/bin/bash
# Quick start script for the Car Rental API

echo "🚗 Car Rental API - Setup Script"
echo "================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

echo "📥 Instalando dependências..."
pip install -r requirements.txt

echo "🗄️  Executando migrations..."
python3 manage.py migrate

echo "📊 Carregando dados de exemplo..."
python3 manage.py shell < init_data.py

echo ""
echo "✅ Setup completo!"
echo ""
echo "Para iniciar o servidor, execute:"
echo "  python manage.py runserver"
echo ""
echo "Para executar testes:"
echo "  python manage.py test rentals"
echo "  # or"
echo "  pytest"
echo ""
echo "API estará disponível em: http://localhost:8000/api/"
echo "Admin panel em: http://localhost:8000/admin/"
echo ""

