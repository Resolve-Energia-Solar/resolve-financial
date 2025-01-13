import os
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from django.template.loader import render_to_string
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMessage
from django.contrib.auth.forms import UserCreationForm


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
    add_form = UserCreationForm
    list_display = ("username", "complete_name", "email", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "complete_name", "email", "first_document")
    readonly_fields = ("last_login", "date_joined")
    inlines = [PhoneNumberInline]

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
    actions = ["send_invitation"]

    def send_invitation(self, request, queryset):

        token_generator = PasswordResetTokenGenerator()

        for user in queryset:
            
            token = token_generator.make_token(user)
            reset_url = os.environ.get('FRONTEND_RESET_PASSWORD_URL')
            reset_url_with_token = f"{reset_url}?token={token}&uid={user.pk}"

            context = {
                'user': user,
                'invitation_link': reset_url_with_token
            }

            subject = 'Você foi convidado para o sistema'
            html_content = render_to_string('invitation-email.html', context)
            
            # Configura o e-mail como HTML
            email = EmailMessage(
                subject=subject,
                body=html_content,
                to=[user.email]
            )
            email.content_subtype = "html"
            email.send()
        
        self.message_user(request, "Convite(s) enviado(s) com sucesso.")

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