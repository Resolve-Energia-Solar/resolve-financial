import os
from django.contrib import admin
import requests

from .models import Financier, FranchiseInstallment, Payment, PaymentInstallment, FinancialRecord
from .task import send_to_omie_task, resend_approval_request_to_responsible_task


@admin.register(Financier)
class FinancierAdmin(admin.ModelAdmin):
    list_display = ('name', 'cnpj', 'phone', 'email', 'is_deleted', 'created_at')
    search_fields = ('name', 'cnpj', 'email')
    list_filter = ('is_deleted', 'created_at')
    ordering = ('-created_at',)


class PaymentInstallmentInline(admin.StackedInline):
    model = PaymentInstallment
    extra = 1


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('sale', 'value', 'payment_type', 'financier', 'due_date', 'created_at')
    search_fields = ('sale__customer__name', 'payment_type', 'financier__name')
    list_filter = ('payment_type', 'due_date', 'created_at')
    ordering = ('-created_at',)
    inlines = [PaymentInstallmentInline]


@admin.register(PaymentInstallment)
class PaymentInstallmentAdmin(admin.ModelAdmin):
    list_display = ('payment', 'installment_value', 'installment_number', 'due_date', 'is_paid', 'paid_at', 'created_at')
    search_fields = ('payment__sale__customer__name', 'installment_number')
    list_filter = ('is_paid', 'due_date', 'created_at')
    ordering = ('-created_at',)
    actions = ['mark_as_paid']

    def mark_as_paid(self, request, queryset):
        for installment in queryset:
            installment.is_paid = True
            installment.save()
        self.message_user(request, "Parcelas selecionadas foram marcadas como pagas.")
    mark_as_paid.short_description = "Marcar parcelas selecionadas como pagas"


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 1

    
@admin.register(FranchiseInstallment)
class FranchiseInstallmentAdmin(admin.ModelAdmin):
    list_display = ('sale', 'status', 'is_paid', 'installment_value', 'created_at', 'difference_value', 'margin_7', 'percentage', 'total_value', 'transfer_percentage')
    search_fields = ('sale__customer__name', 'status')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)
    actions = ['mark_as_paid']
    
    def total_value(self, obj):
        return obj.total_value

    def percentage(self, obj):
        return obj.percentage if obj.percentage else 0
    
    def difference_value(self, obj):
        return obj.difference_value if obj.difference_value else 0
    
    def margin_7(self, obj):
        return obj.margin_7 if obj.margin_7 else 0
    
    def installment_value(self, obj):
        return obj.installment_value if obj.installment_value else 0
    
    def transfer_percentage(self, obj):
        return obj.transfer_percentage if obj.transfer_percentage else 0

    def mark_as_paid(self, request, queryset):
        for installment in queryset:
            installment.status = 'PA'
            installment.save()
        self.message_user(request, "Parcelas selecionadas foram marcadas como pagas.")
    mark_as_paid.short_description = "Marcar parcelas selecionadas como pagas"



@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display = ('protocol', 'integration_code', 'status', 'responsible_status', 'payment_status', 'value', 'due_date', 'created_at')
    search_fields = ('integration_code', 'protocol', ...)
    list_filter = ('status', 'responsible_status', 'payment_status', 'due_date', 'created_at')
    ordering = ('-created_at',)
    actions = ['send_to_omie', 'resend_approval_request_to_responsible']

    def send_to_omie(self, request, queryset):
        for record in queryset:
            if record.integration_code is not None and record.responsible_status == 'A' and record.payment_status == 'P':
                send_to_omie_task.delay(record.id)
                self.message_user(request, f"Tarefa para enviar o registro {record.protocol} agendada.", level='info')
            else:
                self.message_user(request, f"O registro {record.protocol} não atende aos critérios para envio.", level='warning')
    send_to_omie.short_description = "Enviar registros selecionados para o Omie"

    def resend_approval_request_to_responsible(self, request, queryset):
        for record in queryset:
            if record.responsible_status == 'P':
                resend_approval_request_to_responsible_task.delay(record.id)
                self.message_user(request, f"Tarefa para reenviar o convite para o registro {record.protocol} agendada.", level='info')
            else:
                self.message_user(request, f"O registro {record.protocol} não está com o status do responsável pendente.", level='warning')
    resend_approval_request_to_responsible.short_description = "Reenviar solicitação ao responsável"
