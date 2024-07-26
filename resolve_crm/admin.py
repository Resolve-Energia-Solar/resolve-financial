from django.contrib import admin
from .models import Board, Column, Lead, Task, Attachment


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ("board", "name", "order")


"""
@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("lead", "task", "order")
"""


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "contact_email", "origin", "responsible")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("lead", "title", "delivery_date", "description", "status", "task_type")


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("task", "file", "description")
