from django.contrib import admin

from financial.admin import PaymentInline
from .models import ComercialProposal, ContractSubmission, ContractTemplate, Lead, MarketingCampaign, ProjectStep, Step, Task, Project, Sale, Origin
from logistics.admin import ProjectMaterialsInline, SaleProductInline


@admin.register(Origin)
class OriginAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "contact_email", "origin", "seller")
    
    def save_model(self, request, obj, form, change):
        obj.save(current_user=request.user)
        form.save_m2m()  


@admin.register(ComercialProposal)
class ComercialProposalAdmin(admin.ModelAdmin):
    list_display = ("id", "lead", "due_date", "value", "status", "created_by", "created_at")
    search_fields = ("lead__name", "status", "created_by__username")
    list_filter = ("status", "due_date", "created_at")
    inlines = [SaleProductInline]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("customer" ,"contract_number", "total_value", "total_paid","signature_date", "billing_date", "created_at")
    inlines = [SaleProductInline, PaymentInline]
    search_fields = ("contract_number", "customer__username", "seller__username")
    list_filter = ("payment_status", "status", "created_at")
    ordering = ("-created_at",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("lead", "title", "delivery_date", "description", "status", "task_type")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("sale", "product", "created_at")
    inlines = [ProjectMaterialsInline]


@admin.register(ContractSubmission)
class ContractSubmissionAdmin(admin.ModelAdmin):
    list_display = ("sale", "status", "key_number", "finished_at")
    search_fields = ("sale__contract_number", "key_number")
    list_filter = ("finished_at",)
    ordering = ("-finished_at",)


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "default_duration_days")
    list_filter = ("default_duration_days",)
    search_fields = ("name",)
    ordering = ("order",)


@admin.register(ProjectStep)
class ProjectStepAdmin(admin.ModelAdmin):
    list_display = ("project", "step", "deadline")
    search_fields = ("project_number", "step__name")
    list_filter = ("deadline",)
    ordering = ("-deadline",)


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "person_type")
    list_filter = ("is_active", "person_type")
    search_fields = ("name","template")
    ordering = ("name",)
    

@admin.register(MarketingCampaign)
class MarketingCampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "start_datetime", "end_datetime")
    search_fields = ("name",)
    list_filter = ("start_datetime", "end_datetime")
    ordering = ("-start_datetime",)
    