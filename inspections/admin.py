from django.contrib import admin
from .models import RoofType
# Register your models here.


@admin.register(RoofType)
class RoofTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_deleted", "created_at")
    list_filter = ("is_deleted",)
    search_fields = ("name", "is_deleted", "created_at")