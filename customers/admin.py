from django.contrib import admin

from customers.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "first_name", "last_name", "is_staff"]
    search_fields = ["id", "email", "first_name", "last_name"]
    readonly_fields = ["id"]
