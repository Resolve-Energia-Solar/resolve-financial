from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType

from core.models import Process, ProcessBase
from core.task import create_process_async
from financial.admin import PaymentInline
from logistics.models import SaleProduct
from .models import (
    ComercialProposal,
    ContractSubmission,
    ContractTemplate,
    Lead,
    MarketingCampaign,
    ProjectStep,
    Reason,
    Reward,
    Step,
    Task,
    Project,
    Sale,
    Origin,
)
from logistics.admin import ProjectMaterialsInline, SaleProductInline


@admin.action(description="Criar processos para os projetos dessa venda")
def criar_processos_para_venda(modeladmin, request, queryset):
    modelo_id = 1

    try:
        modelo = ProcessBase.objects.get(id=modelo_id)
    except ProcessBase.DoesNotExist:
        messages.error(request, "Modelo de processo não encontrado.")
        return

    content_type = ContentType.objects.get_for_model(Project)

    for venda in queryset:
        if not venda.signature_date:
            messages.warning(request, f"Venda {venda.id} sem data de assinatura.")
            continue

        projects = Project.objects.filter(sale=venda)
        existing_process_ids = set(
            Process.objects.filter(
                content_type=content_type,
                object_id__in=projects.values_list("id", flat=True),
            ).values_list("object_id", flat=True)
        )

        for project in projects:
            if project.id in existing_process_ids:
                continue

            create_process_async.delay(
                process_base_id=modelo.id,
                content_type_id=content_type.id,
                object_id=project.id,
                nome=f"Processo {modelo.name} {venda.contract_number} - {venda.customer.complete_name}",
                descricao=modelo.description,
                user_id=venda.customer.id if venda.customer else None,
                completion_date=venda.signature_date.isoformat(),
            )

    messages.success(request, "Processos sendo criados em segundo plano.")


@admin.register(Origin)
class OriginAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "contact_email", "origin", "seller")
    search_fields = ("name",)
    autocomplete_fields = (
        "addresses",
        "customer",
        "origin",
        "seller",
        "sdr",
        "column",
    )

    def save_model(self, request, obj, form, change):
        obj.save(current_user=request.user)
        form.save_m2m()


@admin.register(ComercialProposal)
class ComercialProposalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "lead",
        "due_date",
        "value",
        "status",
        "created_by",
        "created_at",
    )
    search_fields = ("lead__name", "status", "created_by__username", "lead__name")
    autocomplete_fields = ("lead", "products", "created_by")
    list_filter = ("status", "due_date", "created_at")
    inlines = [SaleProductInline]


@admin.action(description="Criar projetos para as vendas selecionadas")
def criar_projetos_para_venda(modeladmin, request, queryset):
    created_count = 0

    for sale in queryset:
        sale_products = SaleProduct.objects.filter(sale=sale)

        if not sale_products.exists():
            messages.warning(request, f"Venda {sale.id} não possui produtos.")
            continue

        existing_projects = Project.objects.filter(sale=sale).values_list(
            "product_id", flat=True
        )

        projects_to_create = [
            Project(sale=sale, product=sp.product)
            for sp in sale_products
            if sp.product_id not in existing_projects
        ]

        if projects_to_create:
            Project.objects.bulk_create(projects_to_create)
            created_count += len(projects_to_create)

    messages.success(request, f"✅ {created_count} projeto(s) criado(s) com sucesso.")


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "customer",
        "contract_number",
        "total_value",
        "signature_date",
        "billing_date",
        "created_at",
    )
    autocomplete_fields = [
        "customer",
        "seller",
        "sales_supervisor",
        "sales_manager",
        "supplier",
        "branch",
        "marketing_campaign",
        "cancellation_reasons",
        "products",
    ]
    inlines = [SaleProductInline, PaymentInline]
    search_fields = (
        "contract_number",
        "customer__complete_name",
        "seller__complete_name",
    )
    list_filter = ("payment_status", "status", "created_at")
    ordering = ("-created_at",)
    actions = [criar_processos_para_venda, criar_projetos_para_venda]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "lead",
        "title",
        "delivery_date",
        "description",
        "status",
        "task_type",
    )
    autocomplete_fields = [
        "lead",
        "members",
    ]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("sale", "product", "created_at")
    autocomplete_fields = [
        "sale",
        "product",
        "designer",
        "inspection",
        "homologator",
        "materials",
        "registered_circuit_breaker",
    ]
    search_fields = (
        "sale__contract_number",
        "product__name",
        "sale__customer__complete_name",
        "project_number",
    )
    inlines = [ProjectMaterialsInline]


@admin.register(ContractSubmission)
class ContractSubmissionAdmin(admin.ModelAdmin):
    list_display = ("sale", "status", "key_number", "finished_at", "submit_datetime")
    search_fields = (
        "sale__contract_number",
        "key_number",
        "sale__customer__complete_name",
    )
    list_filter = ("finished_at",)
    ordering = ("-finished_at",)
    autocomplete_fields = ["sale"]


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
    autocomplete_fields = ["project", "step"]


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "person_type")
    list_filter = ("is_active", "person_type")
    search_fields = ("name", "template")
    ordering = ("name",)
    autocomplete_fields = ("branches",)


@admin.register(MarketingCampaign)
class MarketingCampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "start_datetime", "end_datetime")
    search_fields = ("name",)
    list_filter = ("start_datetime", "end_datetime")
    ordering = ("-start_datetime",)


@admin.register(Reason)
class ReasonAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("name",)
