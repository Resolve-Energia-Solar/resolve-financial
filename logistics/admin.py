from django.contrib import admin
from .models import MaterialTypes, Materials, ProjectMaterials, SalesMaterials, SolarEnergyKit


@admin.register(MaterialTypes)
class MaterialTypesAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_deleted', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('is_deleted', 'created_at')


@admin.register(Materials)
class MaterialsAdmin(admin.ModelAdmin):
    list_display = ('bar_code', 'description', 'type', 'measure_unit', 'is_serialized', 'is_deleted', 'created_at')
    search_fields = ('bar_code', 'description', 'type__name')
    list_filter = ('is_serialized', 'is_deleted', 'created_at')


@admin.register(SolarEnergyKit)
class SolarEnergyKitAdmin(admin.ModelAdmin):
    list_display = ('inversors_model', 'inversor_amount', 'modules_model', 'modules_amount', 'branch', 'roof_type', 'price', 'is_default', 'is_deleted', 'created_at')
    search_fields = ('inversors_model__description', 'modules_model__description', 'branch__name', 'roof_type__name')
    list_filter = ('is_default', 'is_deleted', 'created_at')


@admin.register(SalesMaterials)
class SalesMaterialsAdmin(admin.ModelAdmin):
    list_display = ('material', 'amount', 'material_class', 'is_deleted', 'created_at')
    search_fields = ('material__description', 'material_class')
    list_filter = ('is_deleted', 'created_at')


@admin.register(ProjectMaterials)
class ProjectMaterialsAdmin(admin.ModelAdmin):
    list_display = ('project', 'material', 'amount', 'is_deleted', 'created_at')
    search_fields = ('project__name', 'material__description')
    list_filter = ('is_deleted', 'created_at')