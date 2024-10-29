import decimal
from django.db import models
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords


class Financier(models.Model):
    name = models.CharField("Nome", max_length=200, null=False, blank=False)
    cnpj = models.CharField("CNPJ", max_length=20, null=True, blank=True)
    address = models.ForeignKey("accounts.Address", on_delete=models.CASCADE, verbose_name="Endereço")
    phone = models.CharField("Telefone", max_length=20)
    email = models.EmailField("E-mail")
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    class Financier:
        verbose_name = "Financiadora"
        verbose_name_plural = "Financiadoras"
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class Payment(models.Model):

    TYPE_CHOICES = [
        ("C", "Crédito"),
        ("D", "Débito"),
        ("B", "Boleto"),
        ("F", "Financiamento"),
        ("PI", "Parcelamento interno")
    ]

    INVOICE_STATUS_CHOICES = [
        ("E", "Emitida"),
        ("L", "Liberada"),
        ("P", "Pendente"),
        ("C", "Cancelada"),
    ]

    sale = models.ForeignKey("resolve_crm.Sale", on_delete=models.CASCADE, verbose_name="Venda", related_name="payments")
    value = models.DecimalField("Valor", max_digits=20, decimal_places=6, default=0.000000)
    payment_type = models.CharField("Tipo de Pagamento", choices=TYPE_CHOICES, max_length=2)
    financier = models.ForeignKey("financial.Financier", on_delete=models.CASCADE, verbose_name="Financiadora", blank=True, null=True)
    due_date = models.DateField("Data de Vencimento")
    invoice_status = models.CharField(
        "Status da Nota Fiscal", 
        max_length=1, 
        choices=INVOICE_STATUS_CHOICES, 
        default="P"
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    @property
    def is_paid(self):
        return all(installment.is_paid for installment in self.installments.all())

    @property
    def total_paid(self):
        return sum(installment.installment_value for installment in self.installments.filter(is_paid=True))

    @property
    def percentual_paid(self):
        if self.value == 0:
            return 0
        return round(self.total_paid / decimal.Decimal(self.value), 4)
    
    def __str__(self):
        return f"{self.sale.customer} - {self.payment_type} - {self.value}"
    
    def clean(self):
        if self.payment_type == "F" and not self.financier:
            raise ValidationError("Pagamentos do tipo financiamento devem ter uma financiadora.")
        return super().clean()

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ["-created_at"]


class PaymentInstallment(models.Model):
    payment = models.ForeignKey("financial.Payment", on_delete=models.CASCADE, verbose_name="Pagamento", related_name="installments")
    installment_value = models.DecimalField("Valor", max_digits=20, decimal_places=6, default=0.000000)
    installment_number = models.PositiveSmallIntegerField("Número da Parcela")
    due_date = models.DateField("Data de Vencimento")
    is_paid = models.BooleanField("Pago", default=False)
    paid_at = models.DateTimeField("Pago em", auto_now_add=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.payment.sale.customer} - Parcela {self.installment_number}: {self.installment_value}"
    
    def clean(self):
        super().clean()
        total_installments_value = sum(installment.installment_value for installment in self.payment.installments.exclude(id=self.id))
        if total_installments_value + self.installment_value > self.payment.value:
            raise ValidationError("A soma do valor das parcelas, incluindo esta nova parcela, não pode ser maior que o valor do pagamento.")

    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"
        ordering = ["-payment__created_at", "installment_number"]
