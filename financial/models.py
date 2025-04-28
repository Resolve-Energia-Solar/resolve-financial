import decimal
from django.db import models
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import validate_email


class Financier(models.Model):
    name = models.CharField("Nome", max_length=200, null=False, blank=False)
    cnpj = models.CharField("CNPJ", max_length=20, null=True, blank=True)
    address = models.ForeignKey(
        "accounts.Address", on_delete=models.PROTECT, verbose_name="Endereço", blank=True, null=True
    )
    phone = models.CharField("Telefone", max_length=20, null=True, blank=True)
    email = models.EmailField("E-mail", null=True, blank=True)
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
        ("PI", "Parcelamento interno"),
        ("P", "Pix"),
        ("T", "Transferência Bancária"),
        ("DI", "Dinheiro"),
        ("PA", "Poste auxiliar"),
        ("RO", "Repasse de Obra"),
    ]

    INVOICE_STATUS_CHOICES = [
        ("E", "Emitida"),
        ("L", "Liberada"),
        ("P", "Pendente"),
        ("C", "Cancelada"),
    ]
    borrower = models.ForeignKey(
        get_user_model(), on_delete=models.PROTECT, verbose_name="Tomador"
    )
    sale = models.ForeignKey(
        "resolve_crm.Sale",
        on_delete=models.PROTECT,
        verbose_name="Venda",
        related_name="payments",
    )
    value = models.DecimalField(
        "Valor", max_digits=20, decimal_places=6, default=0.000000
    )
    payment_type = models.CharField(
        "Tipo de Pagamento", choices=TYPE_CHOICES, max_length=2
    )
    financier = models.ForeignKey(
        "financial.Financier",
        on_delete=models.PROTECT,
        verbose_name="Financiadora",
        blank=True,
        null=True,
    )
    due_date = models.DateField("Data de Vencimento")
    observation = models.TextField("Observação", null=True, blank=True)
    invoice_status = models.CharField(
        "Status da Nota Fiscal",
        max_length=1,
        choices=INVOICE_STATUS_CHOICES,
        default="P",
    )
    
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()

    @property
    def is_paid(self):
        return all(installment.is_paid for installment in self.installments.all())

    @property
    def total_paid(self):
        return sum(
            installment.installment_value
            for installment in self.installments.filter(is_paid=True)
        )

    @property
    def percentual_paid(self):
        if self.value == 0:
            return 0
        return round(self.total_paid / decimal.Decimal(self.value), 4)

    def __str__(self):
        return f"{self.sale.customer} - {self.payment_type} - {self.value}"

    def clean(self):
        if self.payment_type == "F" and not self.financier:
            raise ValidationError(
                "Pagamentos do tipo financiamento devem ter uma financiadora."
            )
        return super().clean()

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ["-created_at"]



class PaymentInstallment(models.Model):
    payment = models.ForeignKey(
        "financial.Payment",
        on_delete=models.CASCADE,
        verbose_name="Pagamento",
        related_name="installments",
    )
    installment_value = models.DecimalField(
        "Valor", max_digits=20, decimal_places=6, default=0.000000
    )
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
        total_installments_value = sum(
            installment.installment_value
            for installment in self.payment.installments.exclude(id=self.id)
        )
        if total_installments_value + self.installment_value > self.payment.value:
            raise ValidationError(
                "A soma do valor das parcelas, incluindo esta nova parcela, não pode ser maior que o valor do pagamento."
            )

    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"
        ordering = ["-payment__created_at", "installment_number"]


class FranchiseInstallment(models.Model):
    sale = models.ForeignKey(
        "resolve_crm.Sale",
        on_delete=models.PROTECT,
        verbose_name="Venda",
        related_name="franchise_installments",
    )
    status = models.CharField(
        "Status",
        max_length=2,
        choices=[("PE", "Pendente"), ("PG", "Pago")],
        default="PE",
    )
    installment_value = models.DecimalField(
        "Valor da Parcela",
        max_digits=20,
        decimal_places=6,
        default=0.000000,
        blank=False,
        null=False,
    )
    is_paid = models.BooleanField("Pago", default=False)
    paid_at = models.DateTimeField("Pago em", null=True, blank=True)
    observation = models.TextField("Observação", null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    
    def payments_methods(self):
        return [
            {
                "payment_type": payment.payment_type, "financier": payment.financier.name if payment.financier else None
            }
            for payment in self.sale.payments.all()
        ]
    
    
    @property
    def is_payment_released(self):
        return all(project.is_released_to_engineering for project in self.sale.projects.all())

    @property
    def transfer_percentage(self):
        if not self.sale:
            return Decimal("0.00")

        if self.sale.transfer_percentage:
            return self.sale.transfer_percentage

        if self.sale.branch and self.sale.branch.transfer_percentage:
            return self.sale.branch.transfer_percentage

        return Decimal("0.00")

    @property
    def difference_value(self):
        """
        Calcula a diferença entre o valor total da venda e a soma dos valores de referência dos produtos.
        Retorna 0 se valores forem inválidos.
        """
        if not self.sale or not self.sale.total_value:
            return Decimal("0.00")

        reference_values = self.sale.sale_products.all().values_list(
            "reference_value", flat=True
        )
        valid_values = [value for value in reference_values if value is not None]
        return self.sale.total_value - sum(valid_values)

    
    def reference_value(self):
        reference_values = self.sale.sale_products.all().values_list("reference_value", flat=True)
        valid_values = [value for value in reference_values if value is not None]
        return sum(valid_values)


    @property
    def margin_7(self):
        """
        Calcula a margem de 7% sobre a diferença de valor.
        """
        if self.difference_value <= 0:
            return Decimal("0.00")
        return self.difference_value * Decimal("0.07")

    @property
    def total_value(self):
        if not self.sale or not self.sale.transfer_percentage and not self.sale.branch.transfer_percentage:
            return Decimal("0.00")

        reference_values = self.sale.sale_products.all().values_list(
            "reference_value", flat=True
        )
        valid_values = [value for value in reference_values if value is not None]
        
        transfer_percentage = self.sale.transfer_percentage if self.sale.transfer_percentage else self.sale.branch.transfer_percentage
        
        if not valid_values:
            return Decimal("0.00")

        reference_value = sum(valid_values)

        if self.difference_value <= 0:
            return round( 
                reference_value * ((transfer_percentage / 100) - self.margin_7), 3
                )

        return round(
            (reference_value * (transfer_percentage / 100))
            - self.margin_7
            + self.difference_value,
            3,
        )

    @property
    def percentage(self):
        """
        Calcula o percentual da parcela em relação ao total da venda.
        """
        if self.total_value == 0:
            return 0.0
        return round((self.installment_value / self.total_value) * 100, 2)

    @staticmethod
    def remaining_percentage(sale):
        """
        Calcula o percentual restante de repasse permitido pela branch da venda.
        """
        if not sale or not sale.transfer_percentage:
            return Decimal("0.00")

        total_repass = sum(
            Decimal(installment.percentage)
            for installment in sale.franchise_installments.all()
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
        return f"{self.sale.customer}%"

    class Meta:
        verbose_name = "Parcela do Franquiado"
        verbose_name_plural = "Parcelas do Franquiado"
        ordering = ["-created_at"]


class FinancialRecord(models.Model):

    STATUS_CHOICES = [
        ("S", "Solicitada"),
        ("E", "Em Andamento"),
        ("P", "Paga"),
        ("C", "Cancelada"),
    ]

    integration_code = models.CharField(
        "Código de Integração", max_length=50, null=True, blank=True
    )
    protocol = models.CharField("Protocolo", max_length=20, null=True, blank=True)
    is_receivable = models.BooleanField(
        "A Receber/A Pagar?",
        help_text="True para contas a receber, False para contas a pagar.",
    )
    status = models.CharField(
        "Status", max_length=1, choices=STATUS_CHOICES, default="S"
    )
    project = models.ForeignKey(
        "resolve_crm.Project",
        on_delete=models.DO_NOTHING,
        verbose_name="Projeto",
        null=True,
        blank=True
    )
    project_integration_code = models.CharField(
        "Código de Integração do Projeto", max_length=8, null=True, blank=True
    )
    value = models.DecimalField("Valor", max_digits=20, decimal_places=2, default=0.00)
    due_date = models.DateField("Data de Vencimento")
    service_date = models.DateField(
        "Data de Prestação do Serviço", null=True, blank=True
    )
    requesting_department = models.ForeignKey("accounts.Department", verbose_name="Departamento Solicitante", on_delete=models.DO_NOTHING, null=True, blank=True)
    department_code = models.CharField("Código do Departamento Causador", max_length=50, null=True, blank=True)
    department_name = models.CharField("Nome do Departamento Causador", max_length=255, null=True, blank=True)
    category_code = models.CharField("Código da Categoria", max_length=20)
    category_name = models.CharField("Nome da Categoria", max_length=255)
    client_supplier_code = models.BigIntegerField("Código do Cliente/Fornecedor")
    bank_details = models.ForeignKey(
        "financial.BankDetails",
        on_delete=models.PROTECT,
        verbose_name="Dados Bancários",
        null=True,
        blank=True,
    )
    client_supplier_name = models.CharField("Nome do Cliente/Fornecedor", max_length=255)
    invoice_number = models.CharField(
        "Número do Documento", max_length=20, null=True, blank=True
    )
    notes = models.TextField("Notas", null=True, blank=True)
    # Logs
    requester = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        verbose_name="Solicitante",
        related_name="requested_financial_records",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    responsible = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        verbose_name="Responsável",
        related_name="responsible_financial_records",
    )
    responsible_status = models.CharField(
        "Status do Responsável",
        max_length=1,
        choices=[("A", "Aprovado"), ("R", "Reprovado"), ("P", "Pendente")],
        default="P",
    )
    responsible_response_date = models.DateTimeField("Data da Resposta do Gestor", null=True, blank=True)
    responsible_request_integration_code = models.CharField(
        "Código de Integração da Solicitação ao Gestor", max_length=50, null=True, blank=True
    )
    responsible_notes = models.TextField("Notas do Responsável", null=True, blank=True)
    payment_method = models.CharField(
        "Método de Pagamento",
        max_length=1,
        choices=[
            ("B", "Boleto"),
            ("T", "Transferência Bancária"),
            ("E", "Dinheiro em Espécie"),
            ("D", "Cartão de Débito"),
            ("C", "Cartão de Crédito"),
            ("P", "Pix"),
        ],
    )
    payment_status = models.CharField(
        "Status do Pagamento",
        max_length=2,
        choices=[("PG", "Pago"), ("P", "Pendente"), ("C", "Cancelado")],
        default="P"
    )
    paid_at = models.DateTimeField("Data de Pagamento", null=True, blank=True)

    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.protocol:
            self.protocol = self.generate_protocol()
        super().save(*args, **kwargs)

    def generate_protocol(self):
        now = timezone.now()
        return f"{now.year}{now.month}{now.day}{now.hour}{now.minute}{now.second}{now.microsecond}"

    def __str__(self):
        tipo = "A Receber" if self.is_receivable else "A Pagar"
        return f"{tipo} - {self.value} - {self.protocol}"

    class Meta:
        verbose_name = "Conta a Pagar/Receber"
        verbose_name_plural = "Contas a Pagar/Receber"
        ordering = ["-created_at"]
        permissions = [
            ("view_all_payable_financial_records", "Can view all payable financial records"),
            ("view_all_department_payable_financial_records", "Can view all payable financial_records from the department"),
            ("view_financialrecord_attachment", "Can view financial record attachment"),
        ]


class BankDetails(models.Model):
    """
    Modelo para armazenar os detalhes bancários de um cliente ou fornecedor.
    """
    ACCOUNT_TYPE_CHOICES = [
        ("C", "Corrente"),
        ("P", "Poupança"),
        ("X", "PIX"),
    ]

    PIX_KEY_TYPE_CHOICES = [
        ("CPF", "CPF"),
        ("CNPJ", "CNPJ"),
        ("EMAIL", "E-mail"),
        ("PHONE", "Celular/Telefone"),
        ("RANDOM", "Chave Aleatória"),
    ]

    client_supplier_code = models.BigIntegerField("Código do Cliente/Fornecedor")
    financial_instituition = models.CharField("Instituição Financeira", max_length=100, blank=True, null=True)
    agency_number = models.CharField("Número da Agência", max_length=20, blank=True, null=True)
    account_number = models.CharField("Número da Conta", max_length=20, blank=True, null=True)
    account_type = models.CharField(
        "Tipo de Conta",
        max_length=1,
        choices=ACCOUNT_TYPE_CHOICES,
    )
    pix_key_type = models.CharField(
        "Tipo de Chave PIX",
        max_length=10,
        choices=PIX_KEY_TYPE_CHOICES,
        blank=True,
        null=True,
    )
    pix_key = models.CharField("Chave PIX", max_length=100, blank=True, null=True)
    history = HistoricalRecords()

    def clean(self):
        if self.account_type == "X":
            if not self.pix_key or not self.pix_key_type:
                raise ValidationError("A chave PIX e o tipo são obrigatórios para contas do tipo PIX.")
            if self.agency_number or self.account_number:
                raise ValidationError("Agência e conta não devem ser preenchidas para contas do tipo PIX.")
            if self.pix_key_type == "CPF":
                if not self.pix_key.isdigit() or len(self.pix_key) != 11:
                    raise ValidationError("A chave PIX do tipo CPF deve conter 11 dígitos numéricos.")
            elif self.pix_key_type == "CNPJ":
                if not self.pix_key.isdigit() or len(self.pix_key) != 14:
                    raise ValidationError("A chave PIX do tipo CNPJ deve conter 14 dígitos numéricos.")
            elif self.pix_key_type == "EMAIL":
                try:
                    validate_email(self.pix_key)
                except ValidationError:
                    raise ValidationError("A chave PIX do tipo E-mail deve ser um e-mail válido.")
            elif self.pix_key_type == "PHONE":
                if not self.pix_key.isdigit() or len(self.pix_key) != 11:
                    raise ValidationError("A chave PIX do tipo Celular/Telefone deve conter 11 dígitos numéricos, ex: 11999999999.")
            elif self.pix_key_type == "RANDOM":
                if len(self.pix_key) != 32:
                    raise ValidationError("A chave PIX do tipo Aleatória deve conter 32 caracteres.")
        else:
            if not (self.financial_instituition and self.agency_number and self.account_number):
                raise ValidationError("Instituição, agência e conta são obrigatórios para contas Corrente ou Poupança.")

    def __str__(self):
        if self.account_type == "X":
            return f"PIX ({self.get_pix_key_type_display()}): {self.pix_key}"
        return f"{self.financial_instituition} Ag: {self.agency_number} Conta: {self.account_number}"

    class Meta:
        verbose_name = "Dados Bancários"
        verbose_name_plural = "Dados Bancários"
        ordering = ["financial_instituition"]
