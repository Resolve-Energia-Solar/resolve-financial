from django.contrib import admin
from .models import SicoobRequest

@admin.register(SicoobRequest)
class SicoobRequestAdmin(admin.ModelAdmin):
    list_display = ("customer", "status")
    search_fields = ("customer__complete_name", "status")
    autocomplete_fields = ("customer", "managing_partner", "requested_by", "branch")

# admin.site.register(SicoobRequest)