from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib import admin
from django.contrib.sessions.models import Session
from .models import *


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ("__str__",)
    ordering = ("-id",)


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "reusable", "required")
    search_fields = ("name",)
    list_filter = ("reusable", "required")
    ordering = ("name",)


@admin.register(DocumentSubType)
class DocumentSubTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "document_type")
    search_fields = ("name", "document_type__name")
    list_filter = ("document_type",)
    ordering = ("name",)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("document_type", "document_subtype", "status", "file", "created_at")
    list_display_links = ("document_type",)
    search_fields = (
        "file",
        "description",
        "status",
        "document_type__name",
        "document_subtype__name",
    )
    list_filter = ("status", "document_type", "document_subtype", "created_at")
    ordering = ("-created_at",)


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("title", "description")


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "board", "proposals_value")


@admin.register(TaskTemplates)
class TaskTemplatesAdmin(admin.ModelAdmin):
    list_display = ("title", "board", "deadline", "auto_create", "column")
    search_fields = ("title", "board__title", "column__name", "description")
    list_filter = ("board", "auto_create", "column")
    ordering = ("title",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "description",
        "owner",
        "start_date",
        "due_date",
        "is_completed_date",
    )
    search_fields = (
        "title",
        "description",
        "owner",
        "board",
        "start_date",
        "due_date",
        "is_completed_date",
    )


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ("url", "content_type", "event", "is_active")


@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ("model", "id", "app_label")
    list_display_links = ("model", "id", "app_label")
    search_fields = ("model", "id", "app_label")
    list_per_page = 10
    list_max_show_all = 100

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "content_type", "codename")
    list_display_links = ("name", "codename")
    search_fields = ("name", "codename")
    list_filter = ("content_type",)
    list_per_page = 10
    list_max_show_all = 100


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("tag", "color")


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("session_key", "session_data", "expire_date")
    search_fields = ("session_key", "session_data")
    list_filter = ("expire_date",)
    ordering = ("-expire_date",)
    list_per_page = 10
    list_max_show_all = 100


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "content_type", "object_id", "text", "created_at")
    search_fields = ("author", "content_type", "object_id", "text")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    list_per_page = 10
    list_max_show_all = 100


@admin.register(ProcessBase)
class ProcessBaseAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name", "description")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    list_per_page = 10
    list_max_show_all = 100

    class Media:
        js = ("admin/js/edit-steps-json.js",)
        css = {
            "all": ("admin/css/form-check.css",),
        }


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "content_type",
        "object_id",
        "deadline",
        "created_at",
    )
    search_fields = ("name", "description", "content_type", "object_id")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    list_per_page = 10
    list_max_show_all = 100

    class Media:
        js = ("admin/js/edit-steps-json.js",)
        css = {
            "all": ("admin/css/form-check.css",),
        }


@admin.register(StepName)
class StepNameAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("id", "name")
    list_per_page = 10
    list_max_show_all = 100


@admin.register(ContentTypeEndpoint)
class ContentTypeEndpointAdmin(admin.ModelAdmin):
    list_display = (
        "content_type",
        "endpoint",
    )
    search_fields = ("endpoint",)
    list_per_page = 10
    list_max_show_all = 100
