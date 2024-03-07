from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *


admin.site.site_header = "Administração do CRM"
admin.site.site_title = "CRM"
admin.site.index_title = "Administração"


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ("username", "complete_name", "email")
    search_fields = ("username", "complete_name", "email", "cpf")
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at", "last_login", "date_joined") 

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("complete_name", "birth_date", "gender", "cpf", "profile_picture")}),
        ("Contact", {"fields": ("phone", "email")}),
        ("Address", {"fields": ("address",)}),
        ("Employee Info", {"fields": ("contract_type", "branch", "department", "role", "user_manager", "hire_date", "resignation_date")}),
        ("Logs", {"fields": ("created_by", "date_joined", "updated_by", "updated_at")}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("zip_code", "country", "state", "city", "street", "complement", "created_by", "created_at", "updated_by", "updated_at")
    list_display_links = ("zip_code", "country", "state", "city", "street", "complement")
    search_fields = ("zip_code", "country", "state", "city", "street", "complement")
    list_filter = ("country", "state", "city", "created_by", "created_at", "updated_by", "updated_at")
    list_per_page = 10
    list_max_show_all = 100
    date_hierarchy = "created_at"
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at")

    class Media:
        js = ('admin/js/autocomplete_address.js',)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "owner")
    list_display_links = ("name", "address", "owner")
    search_fields = ("name", "address", "owner")
    list_filter = ("owner",)
    list_per_page = 10
    list_max_show_all = 100


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    pass


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "email")
    list_display_links = ("name", "email")
    search_fields = ("name", "email")
    list_per_page = 10
    list_max_show_all = 100