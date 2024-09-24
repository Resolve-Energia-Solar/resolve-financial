from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse_lazy
from simple_history.models import HistoricalRecords
from django.contrib.auth import get_user_model
from accounts.models import Branch


class Lead(models.Model):

    name = models.CharField(
        max_length=200, 
        verbose_name="Nome"
    )
    type = models.CharField(
        max_length=200, 
        verbose_name="Tipo", 
        help_text="Pessoa Física ou Jurídica?", 
        choices=[
            ("PF", "Pessoa Física"), 
            ("PJ", "Pessoa Jurídica")
        ],
        blank=True, 
        null=True 
    )
    byname = models.CharField(
        max_length=200, 
        verbose_name="Apelido", 
        blank=True, 
        null=True
    )
    first_document = models.CharField(
        max_length=20, 
        verbose_name="CPF/CNPJ", 
        blank=True, 
        null=True
    )
    second_document = models.CharField(
        max_length=20, 
        verbose_name="RG/IE", 
        blank=True, 
        null=True
    )
    birth_date = models.DateField(
        verbose_name="Data de Nascimento", 
        blank=True, 
        null=True
    )
    gender = models.CharField(
        max_length=1, 
        verbose_name="Gênero", 
        choices=[
            ("M", "Masculino"), 
            ("F", "Feminino")
        ], 
        blank=True, 
        null=True
    )

    # Lead
    contact_email = models.EmailField(
        verbose_name="E-mail", 
        blank=True, 
        null=True
    )
    phone = models.CharField(
        max_length=20, 
        verbose_name="Telefone"
    )
    addresses = models.ManyToManyField(
        "accounts.Address", 
        verbose_name="Endereços", 
        related_name="lead_addresses",
        blank=True 
    )
    customer = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE, 
        verbose_name="Cliente", 
        related_name="customer_leads", 
        blank=True, 
        null=True
    )
    
    # CRM Information
    origin = models.CharField(
        max_length=200, 
        verbose_name="Origem", 
        blank=True, 
        null=True
    )
    seller = models.ForeignKey(
        "accounts.User", 
        on_delete=models.CASCADE, 
        verbose_name="Vendedor", 
        related_name="lead_seller", 
        blank=True, 
        null=True
    )
    sdr = models.ForeignKey(
        "accounts.User", 
        on_delete=models.CASCADE, 
        verbose_name="SDR", 
        related_name="lead_sdr", 
        blank=True, 
        null=True
    )

    # Kanban
    column = models.ForeignKey(
        "core.Column", 
        on_delete=models.CASCADE, 
        verbose_name="Coluna", 
        blank=True, 
        null=True, 
        related_name="leads"
    )

    # Logs
    is_deleted = models.BooleanField(
        "Deletado", 
        default=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Criado em"
    )
    history = HistoricalRecords()
    
    def attachments(self):
        return Attachment.objects.filter(
            object_id=self.id, 
            content_type=ContentType.objects.get_for_model(self)
        )
    
    def __str__(self):
        return self.name

    def save(self, current_user=None, *args, **kwargs):
        if not self.id and current_user is not None:
            self.created_by = self.updated_by = current_user
        elif current_user is not None:
            self.updated_by = current_user
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse_lazy('resolve_crm:lead_detail', kwargs={'pk': self.pk})

    def get_detail_api_url(self):
        return reverse_lazy('api:lead-detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"


class Task(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, verbose_name="Lead")
    title = models.CharField(max_length=200, verbose_name="Título")
    delivery_date = models.DateTimeField(verbose_name="Data de Entrega")
    description = models.TextField(verbose_name="Descrição")
    status = models.CharField(max_length=200, verbose_name="Status", choices=[("P", "Pendente"), ("D", "Desenvolvimento"), ("F", "Finalizado")])
    task_type = models.CharField(max_length=1, verbose_name="Tipo de Atividade", choices=[("L", "Ligar"), ("R", "Responder"), ("E", "E-mail"), ("V", "Visitar"), ("T", "Tentar passar crédito"), ("I", "Vistoria")])
    members = models.ManyToManyField("accounts.User", verbose_name="Membros")
    # Logs
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    history = HistoricalRecords()
    
    def __str__(self):
        return self.title

    def save(self, current_user=None, *args, **kwargs):
        if not self.id and current_user is not None:
            self.created_by = self.updated_by = current_user
        elif current_user is not None:
            self.updated_by = current_user
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse_lazy('resolve_crm:task-detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Tarefa"
        verbose_name_plural = "Tarefas"


class Attachment(models.Model):
    object_id = models.PositiveSmallIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    file = models.FileField("Arquivo", upload_to="resolve_crm/attachments/")
    status = models.CharField("Status", max_length=50, null=True, blank=True)
    document_type = models.ForeignKey("contracts.DocumentType", on_delete=models.CASCADE, verbose_name="Tipo de Documento", null=True, blank=True)
    description = models.TextField("Descrição")
    # Logs
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    def file_name(self):
        return self.file.name.split('/')[-1]

    def file_or_image(self):
        if self.file.name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp')):
            return 'file-image'
        else:
            return 'file'

    def size(self):
        attachment_size = self.file.size
        if attachment_size < 1024 * 1024:
            return f"{attachment_size / 1024:.0f}KB"
        else:
            return f"{attachment_size / (1024 * 1024):.2f}MB"
        
    def __str__(self):
        return self.file.name
    
    class Meta:
        verbose_name = "Anexo"
        verbose_name_plural = "Anexos"


class Contact(models.Model):
    contact_type_choices = [
        ("email", "E-mail"),
        ("sms", "SMS"),
    ]

    contact_type = models.CharField(max_length=10, choices=contact_type_choices, verbose_name="Tipo de Contato")
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, verbose_name="Contato")
    subject = models.CharField(max_length=200, verbose_name="Assunto")
    body = models.TextField(verbose_name="Corpo")
    sent_at = models.DateTimeField(verbose_name="Enviado em")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"


class MarketingCampaign(models.Model):
    name = models.CharField("Nome", max_length=200)
    start_datetime = models.DateTimeField("Data de Início")
    end_datetime = models.DateTimeField("Data de Término")
    description = models.TextField("Descrição")
    banner = models.ImageField("Banner", upload_to="resolve_crm/img/marketing_campaign/")
    is_deleted = models.BooleanField("Deletado", default=False)
    
    def get_absolute_url(self):
        return reverse_lazy('resolve_crm:marketing_campaign_detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Campanha de Marketing"
        verbose_name_plural = "Campanhas de Marketing"


class ContractSubmission(models.Model):
    
    submit_datetime = models.DateTimeField("Data e hora do envio")
    status = models.CharField("Status do envio", max_length=1, choices=[("P", "Pendente"), ("A", "Aceito"), ("R", "Recusado")])
    due_date = models.DateField("Prazo para assinatura", auto_now=False, auto_now_add=False)
    link = models.URLField("Link para assinatura")
    
    def __str__(self):
        self.submit_datetime


class Sale(models.Model):

    # Stakeholders
    customer = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Cliente", related_name="customer_sales")
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, verbose_name="Lead", related_name="lead_sales") 
    seller = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Vendedor", related_name="seller_sales")
    sales_supervisor = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Supervisor de Vendas", related_name="supervisor_sales")
    sales_manager = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Gerente de Vendas", related_name="manager_sales")

    # Sale Information
    total_value = models.DecimalField("Valor", max_digits=20, decimal_places=6, default=0.000000)
    contract_number = models.CharField("Número do Contrato", max_length=20, editable=False) #
    signature_date = models.DateField("Data da Assinatura", auto_now=False, auto_now_add=False, null=True, blank=True, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Unidade")
    marketing_campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, verbose_name="Campanha de Marketing", null=True, blank=True)
    is_sale = models.BooleanField("Pré-venda", default=True)
    status = models.CharField("Status da Venda", max_length=2, choices=[("P", "Pendente"), ("F", "Finalizado"), ("EA", "Em Andamento"), ("C", "Cancelado"), ("D", "Distrato")], default="P")

    # Document Information
    is_completed_document = models.BooleanField("Documento Completo", null=True, blank=True)
    # document_situation = models.CharField("Situação do Documento", max_length=256, null=True, blank=True)
    document_completion_date = models.DateTimeField("Data de Conclusão do Documento", null=True, blank=True)

    # Financial Information
    # financial_status = models.CharField("Status Financeiro", max_length=2, choices=[("P", "Pendente"), ("PA", "Parcial"), ("L", "Liquidado")])
    # is_completed_financial = models.BooleanField("Financeiro Completo", null=True, blank=True)
    # financial_completion_date = models.DateTimeField("Data de Conclusão Financeira", null=True, blank=True)
    # project_value = models.DecimalField("Valor do Projeto", max_digits=20, decimal_places=6, default=0.000000)

    # Logs
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    def save(self, current_user=None, *args, **kwargs):
        if not self.contract_number:
            last_sale = Sale.objects.all().order_by('id').last()
            if last_sale:
                last_number = int(last_sale.contract_number.replace('RES', ''))
                self.contract_number = f'RES{last_number + 1:02}'
            else:
                self.contract_number = 'RES01'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
    
    def __str__(self):
        return f'{self.contract_number} - {self.customer}'


class Project(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, verbose_name="Venda")
    designer = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Projetista", related_name="designer_projects", null=True, blank=True)
    project_number = models.CharField("Número do Projeto", max_length=20, null=True, blank=True)
    start_date = models.DateField("Data de Início", null=True, blank=True)
    end_date = models.DateField("Data de Término", null=True, blank=True)
    is_completed = models.BooleanField("Projeto Completo", default=False, null=True, blank=True) #se status estiver finalizado, is_completed = True
    status = models.CharField("Status do Projeto", max_length=2, choices=[("P", "Pendente"), ("F", "Finalizado"), ("EA", "Em Andamento"), ("C", "Cancelado"), ("D", "Distrato")], null=True, blank=True)
    homologator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Homologador", related_name="homologator_projects", null=True, blank=True)
    addresses = models.ManyToManyField("accounts.Address", verbose_name="Endereços", related_name="project_addresses")
    supply_type = models.CharField("Tipo de Fornecimento", choices=[("M", "Monofásico"), ("B", "Bifásico"), ("T", "Trifásico")], max_length=50, null=True, blank=True)
    kwp = models.DecimalField("kWp", max_digits=10, decimal_places=2, null=True, blank=True)
    registered_circuit_breaker = models.ForeignKey('engineering.CircuitBreaker', on_delete=models.CASCADE, related_name="registered_circuit_breaker", verbose_name="Disjuntor Cadastrado", null=True, blank=True)
    instaled_circuit_breaker = models.ForeignKey('engineering.CircuitBreaker', on_delete=models.CASCADE, related_name="instaled_circuit_breaker", verbose_name="Disjuntor Instalado", null=True, blank=True)
    project_circuit_breaker = models.ForeignKey('engineering.CircuitBreaker', on_delete=models.CASCADE, related_name="project_circuit_breaker", verbose_name="Disjuntor do Projeto", null=True, blank=True)
    # input_pattern_value = models.DecimalField("Valor do Padrão de Entrada", max_digits=10, decimal_places=2)

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"
    
    def __str__(self):
        return self.project_number


class Payment(models.Model):
    TYPE_CHOICES = [
        ("C", "Crédito"),
        ("D", "Débito"),
        ("B", "Boleto"),
        ("F", "Financiamento"),
        ("PI", "Parcelamento interno")
    ]
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, verbose_name="Venda", related_name="payments")
    value = models.DecimalField("Valor", max_digits=20, decimal_places=6, default=0.000000)
    payment_type = models.CharField("Tipo de Pagamento",choices=TYPE_CHOICES, max_length=2)
    installments_number = models.PositiveSmallIntegerField("Número de Parcelas")
    financier = models.ForeignKey("Financier", on_delete=models.CASCADE, verbose_name="Financiadora")
    due_date = models.DateField("Data de Vencimento")
    is_paid = models.BooleanField("Pago", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    def valor_parcela(self):
        return self.value / self.installments_number
    
    def __str__(self):
        return f"{self.sale.customer} - {self.payment_type} - {self.value}"
    
    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"


class PaymentInstallment(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, verbose_name="Pagamento")
    installment_value = models.DecimalField("Valor", max_digits=20, decimal_places=6, default=0.000000)
    installment_number = models.PositiveSmallIntegerField("Número da Parcela")
    due_date = models.DateField("Data de Vencimento")
    is_paid = models.BooleanField("Pago", default=False)
    paid_at = models.DateTimeField("Pago em", auto_now_add=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.payment.sale.customer} - Parcela {self.installment_number}: {self.installment_value}"
    
    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"


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
    