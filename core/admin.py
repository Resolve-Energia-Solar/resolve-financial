from django.contrib import admin
from .models import Board, Column
from .models import Task


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