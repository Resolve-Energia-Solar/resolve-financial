from django.contrib import admin
from .models import Materials
from .models import *


class MaterialAttributesInline(admin.TabularInline):
    model = MaterialAttributes
    extra = 0


@admin.register(Materials)
class MaterialsAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'is_deleted', 'created_at')
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('name',)
    inlines = [MaterialAttributesInline]


class ProductMaterialsInline(admin.TabularInline):
    model = ProductMaterials
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'roof_type', 'default', 'is_deleted', 'created_at')
    search_fields = ('name', 'roof_type__name', 'params', 'branch')
    list_filter = ('default', 'is_deleted', 'created_at')
    inlines = [ProductMaterialsInline]


class ProjectMaterialsInline(admin.TabularInline):
    model = ProjectMaterials
    extra = 1
    
    
class SaleProductInline(admin.TabularInline):
    model = SaleProduct
    extra = 1
    
    
# @admin.register(ProjectMaterials)
# class ProjectMaterialsAdmin(admin.ModelAdmin):
#     list_display = ('project', 'material', 'amount', 'is_deleted', 'created_at')
#     search_fields = ('project__name', 'material__description')
#     list_filter = ('is_deleted', 'created_at')
    

# @admin.register(ProductMaterials)
# class ProductMaterialsAdmin(admin.ModelAdmin):
#     list_display = ('product', 'material', 'amount', 'is_deleted', 'created_at')
#     search_fields = ('product__name', 'material__description')
#     list_filter = ('is_deleted', 'created_at')
    