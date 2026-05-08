# Script para inicializar o banco de dados com dados de exemplo
# Executar com: python manage.py shell < init_data.py

from rentals.models import Car
from decimal import Decimal

# Criar carros de exemplo
cars_data = [
    {"brand": "Toyota", "model": "Corolla", "year": 2020, "daily_rate": Decimal("50.00")},
    {"brand": "Honda", "model": "Civic", "year": 2021, "daily_rate": Decimal("55.00")},
    {"brand": "Ford", "model": "Mustang", "year": 2022, "daily_rate": Decimal("100.00")},
    {"brand": "Tesla", "model": "Model 3", "year": 2023, "daily_rate": Decimal("120.00")},
    {"brand": "BMW", "model": "X5", "year": 2021, "daily_rate": Decimal("150.00")},
]

for car_data in cars_data:
    Car.objects.get_or_create(**car_data, defaults={"available": True})

print("Carros de exemplo criados com sucesso!")

