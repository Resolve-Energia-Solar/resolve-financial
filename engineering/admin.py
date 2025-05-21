from django.contrib import admin
from .models import *


@admin.register(Units)
class UnitsAdmin(admin.ModelAdmin):
    list_display = ("project", "name", "type")
    autocomplete_fields = ["project", "supply_adquance", "address"]
    search_fields = ("name",)


@admin.register(SupplyAdequance)
class SupplyAdequanceAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields =("name",)



@admin.register(SituationEnergyCompany)
class SituationEnergyCompanyAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields =("name",)


@admin.register(RequestsEnergyCompany)
class RequestsEnergyCompanyAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "project",
        "unit",
        "request_date",
        "type",
        "status",
        "conclusion_date",
        "request",
        "interim_protocol",
        "final_protocol",
        "requested_by",
    )
    list_filter = ("company",)
    search_fields = ("final_protocol", "project__project_number", "interim_protocol", )
    autocomplete_fields = ["project", "company", "unit", "type", "situation", "requested_by", "request", ]


@admin.register(ResquestType)
class ResquestTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(EnergyCompany)
class EnergyCompanyAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    autocomplete_fields = ["address"]


@admin.register(CivilConstruction)
class CivilConstructionAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "work_responsibility",
        "repass_value",
        "budget_value",
        "shading_percentage",
    )
    list_display_links = ("project",)
    list_editable = (
        "work_responsibility",
        "repass_value",
        "budget_value",
        "shading_percentage",
    )
    list_filter = ("project", "work_responsibility", "is_customer_aware")
    search_fields = ("project__name", "service_description")
    autocomplete_fields = ("project", "financial_records")
    ordering = ("project",)
    fieldsets = (
        (
            "Informações Gerais",
            {
                "fields": (
                    "project",
                    "work_responsibility",
                    "is_customer_aware",
                    "service_description",
                    "shading_percentage",
                ),
            },
        ),
        (
            "Valores",
            {
                "fields": (
                    "repass_value",
                    "budget_value",
                ),
            },
        ),
    )
