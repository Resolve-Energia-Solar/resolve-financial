from django.contrib import admin
from .models import ComercialProposal, Lead, Task, Attachment, Project, Sale, Origin


@admin.register(Origin)
class OriginAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "contact_email", "origin", "seller")


@admin.register(ComercialProposal)
class ComercialProposalAdmin(admin.ModelAdmin):
    list_display = ("lead", "due_date", "value", "status", "created_by", "created_at")
    search_fields = ("lead__name", "status", "created_by__username")
    list_filter = ("status", "due_date", "created_at")


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("total_value", "contract_number")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("lead", "title", "delivery_date", "description", "status", "task_type")


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("file", "description")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    pass