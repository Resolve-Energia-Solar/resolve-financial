from django.contrib import admin

from inspections.models import *

@admin.register(RoofType)
class RoofTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "category")

@admin.register(Forms)
class FormsAdmin(admin.ModelAdmin):
    list_display = ("name", "service")

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("form", "created_at")