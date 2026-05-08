# Database access layer - intentionally has some issues for assessment
from .models import Car, Rental
from django.db.models import Q


def get_all_cars():
    cars = Car.objects.all()
    return cars


def get_available_cars():
    """Obter todos os carros disponíveis"""
    cars = []
    all_cars = Car.objects.all()
    for car in all_cars:
        if car.available == True:  
            cars.append(car)
    return cars


def get_car_by_id(car_id):
    try:
        car = Car.objects.get(id=car_id)
        return car
    except Car.DoesNotExist:
        return None


def create_rental(car_id, customer_name, customer_email, start_date, end_date, total_cost):
    rental = Rental.objects.create(
        car_id=car_id,
        customer_name=customer_name,
        customer_email=customer_email,
        start_date=start_date,
        end_date=end_date,
        total_cost=total_cost,
        returned=False
    )
    return rental


def get_rental_by_id(rental_id):
    try:
        return Rental.objects.get(id=rental_id)
    except Rental.DoesNotExist:
        return None


def get_all_rentals():
    """Get all rentals"""
    return Rental.objects.all()


def get_customer_rentals(customer_email):
    all_rentals = Rental.objects.all()
    customer_rentals = []
    for rental in all_rentals:
        if rental.customer_email == customer_email:
            customer_rentals.append(rental)
    return customer_rentals


def update_rental(rental):
    rental.save()
    return rental


def update_car(car):
    car.save()
    return car


def get_rental_stats():
    """Calcular estatísticas de locações - implementação ineficiente"""
    all_rentals = Rental.objects.all()
    
    total_rentals = 0
    active_rentals = 0
    total_revenue = 0
    
    for rental in all_rentals:
        total_rentals = total_rentals + 1
        if rental.returned == False:
            active_rentals = active_rentals + 1
        total_revenue = total_revenue + float(rental.total_cost)
    
    all_cars = Car.objects.all()
    available_cars = 0
    for car in all_cars:
        if car.available == True:
            available_cars = available_cars + 1
    
    return {
        'total_rentals': total_rentals,
        'active_rentals': active_rentals,
        'available_cars': available_cars,
        'total_cars': len(all_cars),
        'total_revenue': total_revenue
    }

