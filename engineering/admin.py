from django.contrib import admin
from .models import *
    

@admin.register(Units)
class UnitsAdmin(admin.ModelAdmin):
    list_display = ("project", "name", "type")
    

@admin.register(SupplyAdequance)
class SupplyAdequanceAdmin(admin.ModelAdmin):
    list_display = ("name",)
    

@admin.register(SituationEnergyCompany)
class SituationEnergyCompanyAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(RequestsEnergyCompany)
class RequestsEnergyCompanyAdmin(admin.ModelAdmin):
    list_display = ("company", "project", "unit", "request_date", "type", "status", "situation", "conclusion_date", "request", "interim_protocol", "final_protocol", "requested_by")
    

@admin.register(ResquestType)
class ResquestTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(EnergyCompany)
class EnergyCompanyAdmin(admin.ModelAdmin):
    list_display = ("name",)
    
