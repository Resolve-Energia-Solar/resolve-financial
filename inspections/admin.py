from django.contrib import admin

from inspections.models import *

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

@admin.register(BlockTimeAgent)
class BlockTimeAgentAdmin(admin.ModelAdmin):
    list_display = ("agent", 'start_time', 'end_time', 'start_date', 'end_date')

@admin.register(FreeTimeAgent)
class FreeTimeAgentAdmin(admin.ModelAdmin):
    list_display = ("agent", 'start_time', 'end_time', 'day_of_week')

@admin.register(AgentRoute)
class AgentRouteAdmin(admin.ModelAdmin):
    list_display = ("agent", 'status')
