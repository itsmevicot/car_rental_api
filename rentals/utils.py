# Utility functions for business logic
# Note: Some functions lack proper documentation

def calculate_discount(days: int, total: float) -> float:
    """
    Calcular desconto baseado no número de dias de locação
    
    Args:
        days: Número de dias de locação
        total: Total do custo antes do desconto
    
    Returns:
        Valor do desconto
    """
    if days > 7:
        return total * 0.1
    elif days > 3:
        return total * 0.05
    return 0


def calculate_late_fee(late_days, daily_rate):
    return late_days * daily_rate * 1.5


def validate_rental_dates(start_date, end_date):
    pass

