from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib import admin
from .models import *


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'reusable', 'required')
    search_fields = ('name',)
    list_filter = ('reusable', 'required')
    ordering = ('name',)


@admin.register(DocumentSubType)
class DocumentSubTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'document_type')
    search_fields = ('name', 'document_type__name')
    list_filter = ('document_type',)
    ordering = ('name',)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("file", "description")


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("title", "description")


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "board", "proposals_value")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "owner", "start_date", "due_date", "is_completed_date")
    search_fields = ("title", "description", "owner", "board", "start_date", "due_date", "is_completed_date")
    

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
    list_display_links = ("name", "content_type", "codename")
    search_fields = ("name", "content_type", "codename")
    list_filter = ("content_type",)
    list_per_page = 10
    list_max_show_all = 100


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
    
    
@admin.register(TaggedItem)
class TaggedItemAdmin(admin.ModelAdmin):
    list_display = ("tag", "content_type", "object_id")
    search_fields = ("tag", "content_type", "object_id")
    list_filter = ("tag", "content_type", "object_id")