# Seed script for initial car data.
# Run with: python manage.py shell < init_data.py

from decimal import Decimal

from cars.models import Car

cars_data = [
    {"brand": "Toyota", "model": "Corolla", "year": 2020, "daily_rate": Decimal("50.00")},
    {"brand": "Honda", "model": "Civic", "year": 2021, "daily_rate": Decimal("55.00")},
    {"brand": "Ford", "model": "Mustang", "year": 2022, "daily_rate": Decimal("100.00")},
    {"brand": "Tesla", "model": "Model 3", "year": 2023, "daily_rate": Decimal("120.00")},
    {"brand": "BMW", "model": "X5", "year": 2021, "daily_rate": Decimal("150.00")},
    {"brand": "Nissan", "model": "Sentra", "year": 2020, "daily_rate": Decimal("60.00")},
    {"brand": "Chevrolet", "model": "Onix", "year": 2021, "daily_rate": Decimal("45.00")},
    {"brand": "Fiat", "model": "Cronos", "year": 2022, "daily_rate": Decimal("48.00")},
    {"brand": "Renault", "model": "Kwid", "year": 2023, "daily_rate": Decimal("40.00")},
    {"brand": "Peugeot", "model": "208", "year": 2022, "daily_rate": Decimal("58.00")},
    {"brand": "Jeep", "model": "Renegade", "year": 2023, "daily_rate": Decimal("140.00")},
    {"brand": "Toyota", "model": "Yaris", "year": 2021, "daily_rate": Decimal("62.00")},
    {"brand": "Hyundai", "model": "HB20", "year": 2024, "daily_rate": Decimal("57.00")},
    {"brand": "Volkswagen", "model": "Polo", "year": 2023, "daily_rate": Decimal("59.00")},
    {"brand": "Honda", "model": "City", "year": 2024, "daily_rate": Decimal("68.00")},
    {"brand": "Volkswagen", "model": "Tiguan", "year": 2023, "daily_rate": Decimal("350.00")},
    {"brand": "Hyundai", "model": "Tucson", "year": 2023, "daily_rate": Decimal("400.00")},
    {"brand": "Toyota", "model": "Corolla Cross", "year": 2024, "daily_rate": Decimal("320.00")},
    {"brand": "Jeep", "model": "Compass", "year": 2024, "daily_rate": Decimal("380.00")},
    {"brand": "Chevrolet", "model": "Tracker", "year": 2023, "daily_rate": Decimal("310.00")},
    {"brand": "Nissan", "model": "Kicks", "year": 2024, "daily_rate": Decimal("305.00")},
    {"brand": "Volkswagen", "model": "Taos", "year": 2024, "daily_rate": Decimal("360.00")},
    {"brand": "Honda", "model": "HR-V", "year": 2024, "daily_rate": Decimal("395.00")},
    {"brand": "BMW", "model": "X1", "year": 2024, "daily_rate": Decimal("450.00")},
    {"brand": "Volvo", "model": "XC40", "year": 2024, "daily_rate": Decimal("470.00")},
    {"brand": "Audi", "model": "Q3", "year": 2024, "daily_rate": Decimal("600.00")},
    {"brand": "Mercedes-Benz", "model": "C200", "year": 2024, "daily_rate": Decimal("700.00")},
    {"brand": "BMW", "model": "330i", "year": 2024, "daily_rate": Decimal("650.00")},
    {"brand": "Porsche", "model": "Macan", "year": 2024, "daily_rate": Decimal("900.00")},
    {"brand": "Land Rover", "model": "Evoque", "year": 2024, "daily_rate": Decimal("800.00")},
    {"brand": "Audi", "model": "A5", "year": 2024, "daily_rate": Decimal("720.00")},
    {"brand": "Mercedes-Benz", "model": "GLA 200", "year": 2025, "daily_rate": Decimal("760.00")},
    {"brand": "BMW", "model": "X3", "year": 2025, "daily_rate": Decimal("780.00")},
    {"brand": "Lexus", "model": "NX 350h", "year": 2025, "daily_rate": Decimal("820.00")},
    {"brand": "Porsche", "model": "Cayenne", "year": 2025, "daily_rate": Decimal("950.00")},
    {
        "brand": "Land Rover",
        "model": "Discovery Sport",
        "year": 2025,
        "daily_rate": Decimal("880.00"),
    },
    {"brand": "Maserati", "model": "Grecale", "year": 2025, "daily_rate": Decimal("990.00")},
    {"brand": "Tesla", "model": "Model Y", "year": 2025, "daily_rate": Decimal("690.00")},
]

for car_data in cars_data:
    _, created = Car.objects.get_or_create(
        brand=car_data["brand"],
        model=car_data["model"],
        defaults=car_data,
    )

print("Seed data loaded successfully.")
