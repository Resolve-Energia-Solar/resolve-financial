from django.contrib import admin
from .models import Board, Column, Card, Lead, Task, Attachment


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at")


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ("board", "name", "order")
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at")


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("lead", "task", "order")
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at")


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "contact_email", "origin", "responsible")
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("lead", "title", "delivery_date", "description", "status", "task_type", "date")
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at")


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("task", "file", "description")
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at")