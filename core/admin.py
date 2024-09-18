from django.contrib import admin
from .models import Board, BoardStatus, BoardStatusesOrder
from .models import Task


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("title", "description")


@admin.register(BoardStatus)
class BoardStatusAdmin(admin.ModelAdmin):
    list_display = ("status",)


@admin.register(BoardStatusesOrder)
class BoardStatusesOrderAdmin(admin.ModelAdmin):
    list_display = ("board", "status", "order")