from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.forms import CustomUserCreationForm
from django.contrib.auth.models import Group

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
    autocomplete_fields = ["user", "user_manager", "branch", "department", "role"]
    verbose_name = "Funcionário"
    verbose_name_plural = "Funcionários"
    fields = (
        "contract_type",
        "branch",
        "department",
        "role",
        "user_manager",
        "hire_date",
        "resignation_date",
        "related_branches",
    )
    fk_name = "user"


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        "username",
        "complete_name",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "person_type",
        "gender",
        "user_types",
        "employee__contract_type",
        "employee__branch",
        "employee__department",
        "employee__role",
    )
    search_fields = (
        "username",
        "complete_name",
        "email",
        "first_document",
        "second_document",
    )
    autocomplete_fields = (
        "addresses",
        "user_types",
    )
    readonly_fields = ("last_login", "date_joined")
    inlines = [PhoneNumberInline, EmployeeInline]

    fieldsets = (
        ("Usuário", {"fields": ("username", "password", "user_types")}),
        (
            "Informações Pessoais",
            {
                "fields": (
                    "complete_name",
                    "birth_date",
                    "person_type",
                    "gender",
                    "first_document",
                    "second_document",
                    "profile_picture",
                )
            },
        ),
        (
            "Permissões",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Datas Importantes", {"fields": ("last_login", "date_joined")}),
        (
            "Contato",
            {
                "fields": (
                    "email",
                    "addresses",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "user_types",
                    "complete_name",
                    "first_document",
                    "gender",
                    "birth_date",
                    "email",
                    "person_type",
                ),
            },
        ),
    )

    add_form = CustomUserCreationForm

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not change:
            if obj.user_types.filter(name="Funcionário").exists():
                self.send_invitation(request, [obj])

    actions = ["send_invitation"]

    def send_invitation(self, request, queryset):
        for user in queryset:
            send_invitation_email.delay(user.id)
        self.message_user(request, "Convite(s) enfileirado(s) com sucesso.")

    send_invitation.short_description = "Enviar convite"


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "department", "branch")
    search_fields = (
        "user__username",
        "user__complete_name",
        "role__name",
        "department__name",
        "branch__name",
    )
    list_filter = ("role", "department", "branch")
    list_per_page = 10
    list_max_show_all = 100
    autocomplete_fields = (
        "branch",
        "department",
        "role",
        "user_manager",
        "related_branches",
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("zip_code", "country", "state", "city", "street", "complement")
    list_display_links = (
        "zip_code",
        "country",
        "state",
        "city",
        "street",
        "complement",
    )
    search_fields = ("zip_code", "country", "state", "city", "street", "complement")
    list_filter = ("country", "state", "city")
    list_per_page = 10
    list_max_show_all = 100

    class Media:
        js = ("admin/js/autocomplete_address.js",)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "address",
    )
    list_display_links = (
        "name",
        "address",
    )
    search_fields = ("name",)
    list_filter = ("owners",)
    autocomplete_fields = ["owners", "address", "energy_company"]
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
    autocomplete_fields = ("owner",)


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ("country_code", "area_code", "phone_number", "is_main")
    list_display_links = ("country_code", "area_code", "phone_number")
    search_fields = ("country_code", "area_code", "phone_number")
    autocomplete_fields = ("user",)


@admin.register(Squad)
class SquadAdmin(admin.ModelAdmin):
    list_display = ("name", "branch")
    list_display_links = ("name", "branch")
    search_fields = ("name",)
    list_filter = ("branch",)
    autocomplete_fields = (
        "branch",
        "manager",
        "members",
    )


@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
    )
    search_fields = ("name",)


@admin.register(MonthlyGoal)
class MonthlyGoalAdmin(admin.ModelAdmin):
    list_display = (
        "branch",
        "target_value",
        "achieved_value",
        "month_year"
    )
    search_fields = (
        "branch__name",
        "target_value",
        "achieved_value",
        "month_year"
    )
    list_per_page = 10
    list_max_show_all = 100