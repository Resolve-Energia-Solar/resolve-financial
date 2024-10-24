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
    
    class Meta:
        verbose_name = "Financiadora"
        verbose_name_plural = "Financiadoras"
    
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

    sale = models.ForeignKey("resolve_crm.Sale", on_delete=models.CASCADE, verbose_name="Venda", related_name="payments")
    value = models.DecimalField("Valor", max_digits=20, decimal_places=6, default=0.000000)
    payment_type = models.CharField("Tipo de Pagamento", choices=TYPE_CHOICES, max_length=2)
    installments_number = models.PositiveSmallIntegerField("Número de Parcelas", default=1)
    financier = models.ForeignKey("financial.Financier", on_delete=models.CASCADE, verbose_name="Financiadora", blank=True, null=True)
    due_date = models.DateField("Data de Vencimento")
    is_paid = models.BooleanField("Pago", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    def valor_parcela(self):
        return self.value / self.installments_number
    
    def __str__(self):
        return f"{self.sale.customer} - {self.payment_type} - {self.value}"
    
    def clean(self):
        if self.payment_type == "F" and not self.financier:
            raise ValidationError("Pagamentos do tipo financiamento devem ter uma financiadora.")
        return super().clean()
    
    def update_payment_status(self):
        if self.paymentinstallment_set.filter(is_paid=False).exists():
            self.is_paid = False
        else:
            self.is_paid = True
        self.save()

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"


class PaymentInstallment(models.Model):
    payment = models.ForeignKey("financial.Payment", on_delete=models.CASCADE, verbose_name="Pagamento")
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
        total_installments_value = sum(installment.installment_value for installment in self.payment.paymentinstallment_set.all())
        if total_installments_value + self.installment_value > self.payment.value:
            raise ValidationError("A soma do valor das parcelas, incluindo esta nova parcela, não pode ser maior que o valor do pagamento.")
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.payment.update_payment_status()

    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"