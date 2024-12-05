import decimal
from django.db import models
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum
from simple_history.models import HistoricalRecords
from django.contrib.auth import get_user_model
from django.utils import timezone


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
    borrower = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Tomador")
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



class FranchiseInstallment(models.Model):
    sale = models.ForeignKey(
        "resolve_crm.Sale", on_delete=models.CASCADE, verbose_name="Venda", related_name="franchise_installments"
    )
    status = models.CharField(
        "Status", max_length=2, choices=[("PE", "Pendente"), ("PG", "PAGO")], default="PE"
    )
    installment_value = models.DecimalField(
        "Valor da Parcela", max_digits=20, decimal_places=6, default=0.000000, blank=False, null=False
    )
    is_paid = models.BooleanField("Pago", default=False)
    paid_at = models.DateTimeField("Pago em", null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()

    @property
    def difference_value(self):
        """
        Calcula a diferença entre o valor total da venda e a soma dos valores de referência dos produtos.
        """
        reference_values = self.sale.sale_products.all().values_list("reference_value", flat=True)
        # Filtra valores None
        valid_values = [value for value in reference_values if value is not None]
        return self.sale.total_value - sum(valid_values)

    @property
    def margin_7(self):
        """
        Calcula a margem de 7% sobre a diferença de valor.
        """
        if self.difference_value <= 0:
            return Decimal("0.00")
        return self.difference_value * Decimal("0.07")

    @property
    def percentage(self):
        if self.total_value == 0:
            return 0.0
        return round((self.installment_value / self.total_value) * 100, 2)
    
    @property
    def total_value(self):
        reference_values = self.sale.sale_products.all().values_list("reference_value", flat=True)
        if not reference_values:
            return Decimal("0.00")
        
        # Remove valores None antes de calcular
        reference_values = [value for value in reference_values if value is not None]
        
        if not reference_values:  # Se todos forem None, retorna 0
            return Decimal("0.00")
        
        reference_value = sum(reference_values)
        
        if self.difference_value <= 0:
            return reference_value * ((1 - self.sale.transfer_percentage / 100) - self.margin_7 - self.difference_value)
        
        return round((reference_value * (1 - self.sale.transfer_percentage / 100)) - self.margin_7 + self.difference_value, 3)

    
    @property
    def transfer_percentage(self):
        """
        Retorna o percentual de transferência arredondado, ou 0.00 caso seja None.
        """
        if self.sale.transfer_percentage is None:
            return Decimal("0.00")  # Retorna um valor padrão
        return round(self.sale.transfer_percentage, 2)

    @staticmethod
    def remaining_percentage(sale):
        """
        Calcula o percentual restante de repasse permitido pela branch da venda.
        """
        total_repass = sum(
            Decimal(installment.percentage) for installment in sale.franchise_installments.all()
        )
        max_percentage = sale.transfer_percentage
        return max(0, max_percentage - total_repass)

    def clean(self):
        """
        Valida que a soma dos valores das parcelas não ultrapasse o limite total da venda.
        """
        if not self.sale:
            raise ValidationError("A venda associada a esta parcela é obrigatória.")
        if self.total_value:
            total_value = Decimal(self.total_value)
            total_installments = sum(
                Decimal(installment.installment_value)
                for installment in self.sale.franchise_installments.exclude(id=self.id)
            )
            
            # Verificar se o valor desta parcela somado às existentes excede o total
            if total_installments + Decimal(self.installment_value) > total_value:
                raise ValidationError(
                    f"O valor total das parcelas ({total_installments + Decimal(self.installment_value)}) "
                    f"excede o limite permitido de {total_value}. "
                    f"Valor restante disponível: {total_value - total_installments}."
                )

    def save(self, *args, **kwargs):
        """
        Atualiza o status para 'PG' e registra a data de pagamento caso o valor seja pago.
        """
        if self.is_paid:
            self.status = "PG"
            self.paid_at = timezone.now()
            
        if not self.installment_value and not self.pk:
            self.installment_value = self.total_value
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sale.customer} - {self.percentage}%"
    
    class Meta:
        verbose_name = "Parcela do Franquiado"
        verbose_name_plural = "Parcelas do Franquiado"
        ordering = ['-created_at']

