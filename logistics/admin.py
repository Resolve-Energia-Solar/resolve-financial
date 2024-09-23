from django.contrib import admin
from .models import MaterialTypes, Materials, SolarEnergyKit
# Register your models here.


@admin.register(MaterialTypes)
class MaterialTypesAdmin(admin.ModelAdmin):
    pass