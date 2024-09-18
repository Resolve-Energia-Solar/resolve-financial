from django.contrib import admin
from .models import Board, BoardStatus


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("title", "description")


@admin.register(BoardStatus)
class BoardStatusAdmin(admin.ModelAdmin):
    list_display = ("status", "order")
