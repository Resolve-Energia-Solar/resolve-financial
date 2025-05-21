from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from field_services.models import *

@admin.register(RoofType)
class RoofTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    autocomplete_fields = ["members", "main_category"]

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "form")
    search_fields = ("name", "category__name")
    autocomplete_fields = ("category", "form", "deadline")

@admin.register(Forms)
class FormsAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("form", "created_at")
    search_fields = ("form__name", "answerer__complete_name", "schedule__customer__complete_name")
    autocomplete_fields = ("form", "answerer", "schedule")

@admin.register(Deadline)
class DeadlineAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("customer", "schedule_date", "project", "service", "protocol", "schedule_creator", "status", "created_at")
    search_fields = ("project__project_number", "service__name", "protocol", "schedule_creator__complete_name", "customer__complete_name", "project__sale__customer__complete_name")
    readonly_fields = ("display_leads",)
    autocomplete_fields = ("project", "service", "schedule_creator", "parent_schedules", "attachments", "address", "schedule_agent", "branch", "service_opinion", "final_service_opinion", "customer", "products", "leads", "final_service_opinion_user")

    def display_leads(self, obj):
        leads = obj.lead_inspections.all()
        if not leads:
            return "Sem leads"
        html = '<table class="table table-bordered">'
        html += """
            <thead class="thead-light">
                <tr>
                    <th scope="col">Lead</th>
                    <th scope="col">E-mail</th>
                    <th scope="col">Telefone</th>
                </tr>
            </thead>
            <tbody>
        """
        for lead in leads:
            url = reverse(
                f"admin:{lead._meta.app_label}_{lead._meta.model_name}_change",
                args=[lead.pk]
            )
            email = lead.contact_email if lead.contact_email else "-"
            html += f"<tr><td><a href='{url}'>{lead}</a></td><td>{email}</td><td>{lead.phone}</td></tr>"
        html += "</tbody></table>"
        return mark_safe(html)
    display_leads.short_description = "Leads"

@admin.register(BlockTimeAgent)
class BlockTimeAgentAdmin(admin.ModelAdmin):
    list_display = ("agent", 'start_time', 'end_time', 'start_date', 'end_date')
    autocomplete_fields = ("agent",)

@admin.register(FreeTimeAgent)
class FreeTimeAgentAdmin(admin.ModelAdmin):
    list_display = ("agent", 'start_time', 'end_time', 'day_of_week')
    search_fields = ('agent__complete_name',)
    autocomplete_fields = ("agent",)

@admin.register(FormFile)
class FormFileAdmin(admin.ModelAdmin):
    list_display = ("created_at", 'answer', 'field_id')
    search_fields = ("answer__form__name",)
    autocomplete_fields = ("answer",)

@admin.register(ServiceOpinion)
class ServiceOpinionAdmin(admin.ModelAdmin):
    list_display = ("name", "service", "is_final_opinion")
    search_fields = ("name", "service__name")
    autocomplete_fields = ("service",)
    

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("schedule", "agent", "start_time", "end_time", "status")
    search_fields = ("schedule__protocol", "agent__complete_name", "status")
    autocomplete_fields = ("schedule", "agent")