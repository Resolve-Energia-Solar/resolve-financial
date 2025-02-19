from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from field_services.models import *

@admin.register(RoofType)
class RoofTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "form")

@admin.register(Forms)
class FormsAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("form", "created_at")

@admin.register(Deadline)
class DeadlineAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("schedule_date", "project", "service")
    readonly_fields = ("display_leads",)

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

@admin.register(FreeTimeAgent)
class FreeTimeAgentAdmin(admin.ModelAdmin):
    list_display = ("agent", 'start_time', 'end_time', 'day_of_week')
    search_fields = ('agent__complete_name',)

@admin.register(FormFile)
class FormFileAdmin(admin.ModelAdmin):
    list_display = ("created_at", 'answer', 'field_id')

@admin.register(ServiceOpinion)
class ServiceOpinionAdmin(admin.ModelAdmin):
    list_display = ("name", "service")
