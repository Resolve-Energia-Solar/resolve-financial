from django.contrib import admin
from .models import Financier, Payment, PaymentInstallment


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