from django.contrib import admin
from .models import *
    

@admin.register(Units)
class UnitsAdmin(admin.ModelAdmin):
    list_display = ("project", "name", "type")