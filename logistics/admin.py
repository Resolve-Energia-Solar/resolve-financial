from django.contrib import admin
from .models import *


class MaterialAttributesInline(admin.TabularInline):
    model = MaterialAttributes
    extra = 0


@admin.register(Materials)
class MaterialsAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_deleted', 'created_at')
    list_filter = ('is_deleted', 'created_at')
    inlines = [MaterialAttributesInline]
    

class SolarKitMaterialsInline(admin.TabularInline):
    model = SolarKitMaterials
    extra = 0


@admin.register(SolarEnergyKit)
class SolarEnergyKitAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'roof_type', 'price', 'is_default', 'is_deleted', 'created_at')
    search_fields = ('inversors_model__description', 'modules_model__description', 'branch__name', 'roof_type__name')
    list_filter = ('is_default', 'is_deleted', 'created_at')
    inlines = [SolarKitMaterialsInline]


@admin.register(ProjectMaterials)
class ProjectMaterialsAdmin(admin.ModelAdmin):
    list_display = ('project', 'material', 'amount', 'is_deleted', 'created_at')
    search_fields = ('project__name', 'material__description')
    list_filter = ('is_deleted', 'created_at')
    

@admin.register(SaleSolarKits)
class SaleSolarKitsAdmin(admin.ModelAdmin):
    list_display = ('solar_kit', 'amount', 'is_deleted', 'created_at')
    search_fields = ('project__name', 'solar_kit__name')
    list_filter = ('is_deleted', 'created_at')
    

@admin.register(SolarKitMaterials)
class SolarKitMaterialsAdmin(admin.ModelAdmin):
    list_display = ('solar_kit', 'material', 'amount', 'is_deleted', 'created_at')
    search_fields = ('solar_kit__name', 'material__description')
    list_filter = ('is_deleted', 'created_at')
    