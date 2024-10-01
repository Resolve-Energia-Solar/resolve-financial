from django.contrib import admin
from .models import *

@admin.register(CircuitBreaker)
class CircuitBreakerAdmin(admin.ModelAdmin):
    list_display = ("material", "pole", "current")
    

@admin.register(Units)
class UnitsAdmin(admin.ModelAdmin):
    list_display = ("project", "name", "type")