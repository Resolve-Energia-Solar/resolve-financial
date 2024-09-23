from django.contrib import admin
from .models import Lead, Task, Attachment, Project, Sale



"""
@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("lead", "task", "order")
"""

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    pass


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "contact_email", "origin", "seller")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("lead", "title", "delivery_date", "description", "status", "task_type")


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("file", "description")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    pass