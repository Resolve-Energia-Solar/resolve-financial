from django.contrib import admin
from .models import CustomerService


@admin.register(CustomerService)
class CustomerServiceAdmin(admin.ModelAdmin):
    list_display = ("protocol", "customer", "user", "service", "date")
    search_fields = ("protocol", "customer__complete_name", "user")
    list_filter = ("date", "service")
