from django.contrib import admin
from .models import API, Discount, Product, Reel, Media


@admin.register(API)
class APIAdmin(admin.ModelAdmin):
    list_display = ('name', 'url')
    search_fields = ('name',)


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'link')
    search_fields = ('title',)


@admin.register(Reel)
class ReelAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'link')
    search_fields = ('title',)


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'link')
    search_fields = ('title',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price')
    search_fields = ('name',)
