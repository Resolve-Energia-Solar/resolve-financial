from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib import admin

from .models import Board, Column
from .models import Task, Webhook


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("title", "description")


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "board")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "owner", "board", "is_completed", "start_date", "due_date", "is_completed_date")
    list_filter = ("is_completed",)
    search_fields = ("title", "description", "owner", "board", "is_completed", "start_date", "due_date", "is_completed_date")
    

@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ("url", "content_type")


@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ("app_label", "model")
    list_display_links = ("app_label", "model")
    search_fields = ("app_label", "model")
    list_per_page = 10
    list_max_show_all = 100


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "content_type", "codename")
    list_display_links = ("name", "content_type", "codename")
    search_fields = ("name", "content_type", "codename")
    list_filter = ("content_type",)
    list_per_page = 10
    list_max_show_all = 100
