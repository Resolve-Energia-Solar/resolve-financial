from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

admin.site.site_header = "Administração do CRM"
admin.site.site_title = "CRM"
admin.site.index_title = "Administração"


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ("username", "complete_name", "email", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "complete_name", "email", "first_document")
    readonly_fields = ("last_login", "date_joined") 

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("complete_name", "birth_date", "gender", "first_document", "profile_picture")}),
        ("Contact", {"fields": ("phone", "email")}),
        ("Address", {"fields": ("addresses",)}),
        ("Employee Info", {"fields": ("contract_type", "branch", "department", "role", "user_manager", "hire_date", "resignation_date")}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("zip_code", "country", "state", "city", "street", "complement")
    list_display_links = ("zip_code", "country", "state", "city", "street", "complement")
    search_fields = ("zip_code", "country", "state", "city", "street", "complement")
    list_filter = ("country", "state", "city")
    list_per_page = 10
    list_max_show_all = 100

    class Media:
        js = ('admin/js/autocomplete_address.js',)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "address",)
    list_display_links = ("name", "address",)
    search_fields = ("name", "address", "owners")
    list_filter = ("owners",)
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
