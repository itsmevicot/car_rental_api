from django.contrib import admin
from .models import Car, Rental


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['brand', 'model', 'year', 'daily_rate', 'available']
    list_filter = ['available', 'brand']
    search_fields = ['brand', 'model']


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ['id', 'car', 'customer_name', 'customer_email', 'start_date', 'end_date', 'returned']
    list_filter = ['returned', 'start_date']
    search_fields = ['customer_name', 'customer_email']
    date_hierarchy = 'start_date'

