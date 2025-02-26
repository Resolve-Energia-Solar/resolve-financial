import os
import random
import string
from django.contrib.auth.hashers import make_password
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.template.loader import render_to_string
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMessage

from accounts.forms import CustomUserCreationForm

from .models import *
from .task import send_invitation_email


admin.site.site_header = "Administração do CRM"
admin.site.site_title = "CRM"
admin.site.index_title = "Administração"


class PhoneNumberInline(admin.TabularInline):
    model = PhoneNumber
    extra = 1
    verbose_name = "Número de Telefone"
    verbose_name_plural = "Números de Telefone"
    fields = ("country_code", "area_code", "phone_number", "is_main")


class EmployeeInline(admin.StackedInline):
    model = Employee
    extra = 1
    verbose_name = "Funcionário"
    verbose_name_plural = "Funcionários"
    fields = (
        'contract_type',
        'branch',
        'department',
        'role',
        'user_manager',
        'hire_date',
        'resignation_date',
        'related_branches'
    )
    autocomplete_fields = ["role", "department", "branch"]
    fk_name = "user"    


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ("username", "complete_name", "email", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "complete_name", "email", "first_document")
    readonly_fields = ("last_login", "date_joined")
    inlines = [PhoneNumberInline, EmployeeInline]

    fieldsets = (
        ('Usuário', {
            'fields': ('username', 'password', 'user_types')
        }),
        ('Informações Pessoais', {
            'fields': ('complete_name', 'birth_date', 'person_type', 'gender', 'first_document', 'second_document', 'profile_picture')
        }),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Datas Importantes', {
            'fields': ('last_login', 'date_joined')
        }),
        ('Contato', {
            'fields': ('email', 'addresses',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('user_types', 'complete_name', 'first_document', 'gender', 'birth_date', 'email', 'person_type'),
        }),
    )

    add_form = CustomUserCreationForm

    def save_model(self, request, obj, form, change):
        if not change: 
            self.send_invitation(request, [obj])
        super().save_model(request, obj, form, change)
    
    actions = ["send_invitation"]

    def send_invitation(self, request, queryset):
        for user in queryset:
            send_invitation_email.delay(user.id)
        self.message_user(request, "Convite(s) enfileirado(s) com sucesso.")

    send_invitation.short_description = "Enviar convite"


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "department", "branch")
    search_fields = ("user__username", "user__complete_name", "role__name", "department__name", "branch__name")
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
    search_fields = ("name", "address")
    list_filter = ("owners",)
    list_per_page = 10
    list_max_show_all = 100


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "email")
    list_display_links = ("name", "email")
    search_fields = ("name", "email")
    list_per_page = 10
    list_max_show_all = 100


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    pass


@admin.register(Squad)
class SquadAdmin(admin.ModelAdmin):
    pass


@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
