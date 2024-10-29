from django.contrib import admin
from .models import DocumentType, DocumentSubType


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