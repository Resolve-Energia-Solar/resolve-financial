from django.contrib import admin
from .models import CustomerService, LostReason


@admin.register(CustomerService)
class CustomerServiceAdmin(admin.ModelAdmin):
    list_display = ("protocol", "customer", "user", "service", "date")
    search_fields = ("protocol", "customer__complete_name", "user")
    list_filter = ("date", "service")
    autocomplete_fields = ("customer",)


@admin.register(LostReason)
class LostReasonAdmin(admin.ModelAdmin):
    list_display = ("name", "is_deleted", "created_at")
    search_fields = ("name",)
    list_filter = ("is_deleted",)