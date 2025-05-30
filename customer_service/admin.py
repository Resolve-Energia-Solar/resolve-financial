from django.contrib import admin
from .models import CustomerService, LostReason, Ticket, TicketType


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
    
    
@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "deadline", "is_deleted", "created_at")
    search_fields = ("name",)
    list_filter = ("is_deleted",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("project", "responsible", "status", "created_at")
    search_fields = ("project__name", "responsible__complete_name")
    list_filter = ("status",)
    autocomplete_fields = ("project", "responsible")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("project", "responsible")