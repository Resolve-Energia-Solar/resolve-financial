from django.db import models


class PaymentRequest(models.Model):
    protocol = models.CharField("Protocolo", max_length=14)
    requester = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, verbose_name="Requisitante", related_name='requested_payments'
    )
    manager = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, verbose_name="Gestor", related_name='managed_payments'
    )
    department = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, verbose_name="Setor", related_name='department_payments'
    )
    # supplier = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name="Fornecedor", related_name='supplier_payments')
    supplier = models.CharField("Fornecedor", max_length=255)
    id_sale = models.ForeignKey(
        'resolve_crm.Sale', on_delete=models.CASCADE, verbose_name="Venda"
    )
    description = models.TextField("Descrição")
    amount = models.DecimalField("Valor", max_digits=20, decimal_places=6)
    service_date = models.DateField("Data de Serviço")
    due_date = models.DateField("Data de Vencimento")
    category = models.CharField("Categoria", max_length=50)
    causative_department = models.CharField("Departamento Causador", max_length=8, null=True, blank=True)
    payment_method = models.CharField("Forma de Pagamento", max_length=50)
    id_bank_account = models.CharField("Conta Bancária", max_length=8, null=True, blank=True)
    requesting_status = models.CharField("Status da Requisição", max_length=50)
    manager_status = models.CharField("Status do Gestor", max_length=50, null=True, blank=True)
    manager_status_completion_date = models.DateTimeField("Data de Conclusão do Status do Gestor", null=True, blank=True)
    financial_status = models.CharField("Status Financeiro", max_length=50)
    financial_status_completion_date = models.DateTimeField("Data de Conclusão do Status Financeiro", null=True, blank=True)
    invoice_number = models.CharField("Número da Fatura", max_length=255, null=True, blank=True)
    id_omie = models.CharField("ID Omie", max_length=50, null=True, blank=True)
    
    # Logs
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.protocol

    class Meta:
        verbose_name = 'Requisição de Pagamento'
        verbose_name_plural = 'Requisições de Pagamento'
        ordering = ['-created_at']


