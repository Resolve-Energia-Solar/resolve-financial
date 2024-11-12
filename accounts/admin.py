from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

admin.site.site_header = "Administração do CRM"
admin.site.site_title = "CRM"
admin.site.index_title = "Administração"


class PhoneNumberInline(admin.TabularInline):
    model = PhoneNumber
    extra = 1
    verbose_name = "Número de Telefone"
    verbose_name_plural = "Números de Telefone"
    fields = ("country_code", "phone_number", "is_main")


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ("username", "complete_name", "email", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "complete_name", "email", "first_document")
    readonly_fields = ("last_login", "date_joined") 
    inlines = [PhoneNumberInline]

    # fieldsets = (
    #     (None, {"fields": ("username", "password")}),
    #     ("Personal info", {"fields": ("complete_name", "birth_date", "gender", "first_document", "profile_picture")}),
    #     ("Contact", {"fields": ("email",)}),
    #     ("Address", {"fields": ("addresses",)}),
    #     ("User Type Info", {"fields": ("user_types", "person_type", "second_document")}),
    #     ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    # )


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "department", "branch")
    search_fields = ("user", "role", "department", "branch")
    list_filter = ("role", "department", "branch")
    list_per_page = 10
    list_max_show_all = 100


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

@admin.register(PhoneNumber)
class PhoneNumber(admin.ModelAdmin):
    pass


@admin.register(Squad)
class SquadAdmin(admin.ModelAdmin):
    pass


@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")