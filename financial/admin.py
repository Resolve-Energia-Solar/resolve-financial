from django.contrib import admin
from .models import Financier, Payment, PaymentInstallment


@admin.register(Financier)
class FinancierAdmin(admin.ModelAdmin):
    list_display = ('name', 'cnpj', 'phone', 'email', 'is_deleted', 'created_at')
    search_fields = ('name', 'cnpj', 'email')
    list_filter = ('is_deleted', 'created_at')
    ordering = ('-created_at',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('sale', 'value', 'payment_type', 'installments_number', 'financier', 'due_date', 'is_paid', 'created_at')
    search_fields = ('sale__customer__name', 'payment_type', 'financier__name')
    list_filter = ('payment_type', 'is_paid', 'due_date', 'created_at')
    ordering = ('-created_at',)


@admin.register(PaymentInstallment)
class PaymentInstallmentAdmin(admin.ModelAdmin):
    list_display = ('payment', 'installment_value', 'installment_number', 'due_date', 'is_paid', 'paid_at', 'created_at')
    search_fields = ('payment__sale__customer__name', 'installment_number')
    list_filter = ('is_paid', 'due_date', 'created_at')
    ordering = ('-created_at',)
