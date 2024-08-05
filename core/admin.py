from django.contrib import admin
from .models import Board, Column


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("title", "description")


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ("board", "title", "order")
