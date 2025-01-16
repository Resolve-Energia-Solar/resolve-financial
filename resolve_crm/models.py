from decimal import Decimal
from uuid import uuid4
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse_lazy
from django.utils.timezone import now
from core.models import Attachment, DocumentType
from simple_history.models import HistoricalRecords
from django.contrib.auth import get_user_model
from accounts.models import Branch
from financial.models import PaymentInstallment
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta


class Origin(models.Model):
    TYPE_CHOICES = [
        ("IB", "Inbound"),
        ("OB", "Outbound"),
    ]
    name = models.CharField("Nome", max_length=200)
    type = models.CharField("Tipo", max_length=20, choices=TYPE_CHOICES, default="IB")
    is_deleted = models.BooleanField("Deletado", default=False)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Origem"
        verbose_name_plural = "Origens"
        ordering = ['name']


class Lead(models.Model):
    
    FUNNEL_CHOICES = [
        ("N", "Não Interessado"),
        ("P", "Pouco Interessado"),
        ("I", "Interessado"),
        ("M", "Muito Interessado"),
        ("PC", "Pronto para Comprar"),
    ]

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
    origin = models.ForeignKey(
        "resolve_crm.Origin", 
        on_delete=models.CASCADE, 
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
    
    funnel = models.CharField(
        max_length=200, 
        verbose_name="Funil", 
        blank=True, 
        null=True,
        choices=FUNNEL_CHOICES
    )
    
    qualification = models.PositiveIntegerField(
        verbose_name="Qualificação", 
        blank=True, 
        null=True
    )
    
    kwp = models.DecimalField(
        max_digits=20, 
        decimal_places=3, 
        verbose_name="Potência (kWp)", 
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
    
    moved_at = models.DateTimeField(
        "Movido em", 
        blank=True, 
        null=True
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
    # Se for uma atualização (o objeto já tem um ID)
        if self.pk:
            old_lead = Lead.objects.get(pk=self.pk)
            if old_lead.column != self.column:
                self.moved_at = now()
        else:
            # Se for uma criação (não tem um ID), definir moved_at
            self.moved_at = now()

        # Salvar o objeto antes de associar o current_user ou outros campos
        super().save(*args, **kwargs)

        # Atualizar os campos relacionados ao usuário
        if current_user is not None:
            if not self.id:
                self.created_by = current_user
            self.updated_by = current_user
            super().save(*args, **kwargs)  # Salvar novamente para atualizar os campos de auditoria


        
    def get_absolute_url(self):
        return reverse_lazy('resolve_crm:lead_detail', kwargs={'pk': self.pk})

    def get_detail_api_url(self):
        return reverse_lazy('api:lead-detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        ordering = ['-created_at']


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
        verbose_name = "Tarefa do Lead"
        verbose_name_plural = "Tarefas do Lead"
        ordering = ['-created_at']


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
    
    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"
        ordering = ['-sent_at']


class MarketingCampaign(models.Model):
    name = models.CharField("Nome", max_length=200)
    start_datetime = models.DateTimeField("Data de Início")
    end_datetime = models.DateTimeField("Data de Término")
    description = models.TextField("Descrição")
    banner = models.ImageField("Banner", upload_to="resolve_crm/img/marketing_campaign/")
    is_deleted = models.BooleanField("Deletado", default=False)
    
    def get_absolute_url(self):
        return reverse_lazy('resolve_crm:marketing_campaign_detail', kwargs={'pk': self.pk})
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Campanha de Marketing"
        verbose_name_plural = "Campanhas de Marketing"
        ordering = ['-start_datetime']


class ContractSubmission(models.Model):
    sale = models.ForeignKey("resolve_crm.Sale", on_delete=models.CASCADE, verbose_name="Venda", related_name="contract_submissions")
    submit_datetime = models.DateTimeField("Data e hora do envio")
    status = models.CharField("Status do envio", max_length=1, choices=[("P", "Pendente"), ("A", "Aceito"), ("R", "Recusado")])
    due_date = models.DateField("Prazo para assinatura", auto_now=False, auto_now_add=False)
    key_number = models.CharField("Número da Chave", max_length=50, null=True, blank=True)
    request_signature_key = models.CharField("Chave de solicitação de assinatura", max_length=50, null=True, blank=True)
    link = models.URLField("Link para assinatura")
    finished_at = models.DateTimeField("Finalizado em", null=True, blank=True)
    
    def __str__(self):
        return f'{self.sale.customer or "Unknown Customer"} - {self.submit_datetime or "Unknown Date"}'
    
    class Meta:
        verbose_name = "Envio de Contrato"
        verbose_name_plural = "Envios de Contrato"
        ordering = ['-submit_datetime']


class ComercialProposal(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, verbose_name="Lead", related_name="proposals")
    due_date = models.DateField("Prazo para aceitação", auto_now=False, auto_now_add=False)
    value = models.DecimalField("Valor da proposta", max_digits=20, decimal_places=2)
    token = models.UUIDField("Token", editable=False, default=uuid4)
    status = models.CharField("Status da proposta", max_length=1, choices=[("P", "Pendente"), ("A", "Aceita"), ("R", "Recusada")])
    observation = models.TextField("Descrição da proposta", blank=True, null=True)
    products = models.ManyToManyField('logistics.Product', through='logistics.SaleProduct', verbose_name='Produtos')

    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Criado por", related_name="created_proposals")
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    
    def __str__(self):
        return f'{self.value} - {self.lead}'
    
    class Meta:
        verbose_name = "Proposta Comercial"
        verbose_name_plural = "Propostas Comerciais"
        ordering = ['-created_at']


class Sale(models.Model):
    
    PAYMENT_STATUS_CHOICES = [
        ("P", "Pendente"),
        ("L", "Liberado"),
        ("C", "Concluído"),
    ]
    
    # Stakeholders
    customer = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Cliente", related_name="customer_sales")
    seller = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Vendedor", related_name="seller_sales")
    sales_supervisor = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Supervisor de Vendas", related_name="supervisor_sales")
    sales_manager = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Gerente de Vendas", related_name="manager_sales")
    # Sale Information
    total_value = models.DecimalField("Valor", max_digits=20, decimal_places=3, default=0.000)
    payment_status = models.CharField("Status do Pagamento", max_length=2, choices=PAYMENT_STATUS_CHOICES, default="P")
    contract_number = models.CharField("Número do Contrato", max_length=20, editable=False, null=True, blank=True)
    signature_date = models.DateField("Data da Assinatura", auto_now=False, auto_now_add=False, null=True, blank=True, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Unidade")
    marketing_campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, verbose_name="Campanha de Marketing", null=True, blank=True)
    is_pre_sale = models.BooleanField("Pré-venda", default=True) 
    status = models.CharField("Status da Venda", max_length=2, choices=[("P", "Pendente"), ("F", "Finalizado"), ("EA", "Em Andamento"), ("C", "Cancelado"), ("D", "Distrato")], default="P")
    transfer_percentage = models.DecimalField(
        "Porcentagem de Repasse",
        max_digits=7,
        decimal_places=4,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
    )
    
    products = models.ManyToManyField('logistics.Product', through='logistics.SaleProduct', verbose_name='Produtos')

    # is_completed_financial = models.BooleanField("Financeiro Completo", default=False)
    financial_completion_date = models.DateTimeField("Data de Conclusão do Financeiro", null=True, blank=True)

    # Logs
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    @property
    def can_generate_contract(self):
        customer_data = bool(self.customer.first_name and self.customer.last_name and self.customer.email and self.customer.first_document)
        value = 0
        all_payments_have_borrower = True

        for payment in self.payments.all():
            value += payment.value
            if not payment.borrower:
                all_payments_have_borrower = False

        payment_data = value >= self.total_value and all_payments_have_borrower
        have_units = all(project.units.exists() for project in self.projects.all())

        result = customer_data and payment_data and have_units and all_payments_have_borrower

        # Filtrar somente as dependências que estão False
        dependencies = {
            "customer_data": customer_data,
            "payment_data": payment_data,
            "have_units": have_units,
            "all_payments_have_borrower": all_payments_have_borrower,
        }
        failed_dependencies = {key: value for key, value in dependencies.items() if not value}

        return {
            "is_valid": result,
            "failed_dependencies": failed_dependencies
        }
        
    @property
    def total_paid(self):
        total_paid = 0
        installments = PaymentInstallment.objects.filter(payment__sale=self, is_paid=True)
        for installment in installments:
            total_paid += installment.installment_value
        return total_paid

    @property
    def attachments(self):
        return Attachment.objects.filter(
            object_id=self.id, 
            content_type=ContentType.objects.get_for_model(self)
        )

    @property
    def franchise_installments_generated(self):
        return self.franchise_installments.exists()
    
    def missing_documents(self):
        required_documents = DocumentType.objects.filter(required=True)
        missing_documents = []
        if required_documents:
            for document in required_documents:
                if not self.attachments.filter(document_type=document):
                    missing_documents.append({
                        'id': document.id,
                        'name': document.name
                    })
            return missing_documents
        return None
    
    def save(self, current_user=None, *args, **kwargs):
        if not self.contract_number:
            last_sale = Sale.objects.all().order_by('id').last()
            if last_sale:
                last_number = int(last_sale.contract_number.replace('RESOL', '')) if last_sale.contract_number else 0
                self.contract_number = f'RESOL{last_number + 1:02}'
            else:
                self.contract_number = 'RESOL01'

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.contract_number} - {self.customer}'


class Step(models.Model):
    name = models.CharField("Nome da Etapa", max_length=100)
    slug = models.SlugField("Slug", max_length=100)
    default_duration_days = models.PositiveIntegerField("Prazo Padrão (em dias)", default=0)
    description = models.TextField("Descrição da Etapa", null=True, blank=True)
    order = models.PositiveIntegerField("Ordem", default=0)
    
    class Meta:
        verbose_name = "Etapa"
        verbose_name_plural = "Etapas"
    
    def __str__(self):
        return self.name


class Project(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, verbose_name="Venda", related_name="projects")
    product = models.ForeignKey('logistics.Product', on_delete=models.CASCADE, verbose_name="Produto", blank=True, null=True)
    project_number = models.CharField("Número do Projeto", max_length=20, null=True, blank=True)
    plant_integration = models.CharField("ID da Usina", max_length=20, null=True, blank=True)
    designer = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Projetista", related_name="designer_projects", null=True, blank=True)
    designer_status = models.CharField("Status do Projeto de Engenharia", max_length=2, choices=[("P", "Pendente"), ("CO", "Concluído"), ("EA", "Em Andamento"), ("C", "Cancelado"), ("D", "Distrato")], null=True, blank=True)
    designer_coclusion_date = models.DateField("Data de Conclusão do Projeto de Engenharia", null=True, blank=True)
    
    inspection = models.ForeignKey('field_services.Schedule', on_delete=models.CASCADE, verbose_name="Agendamento da Vistoria", null=True, blank=True, related_name="project_field_services")
    # ajustar quando a data de início e término for definida
    start_date = models.DateField("Data de Início", null=True, blank=True)
    end_date = models.DateField("Data de Término", null=True, blank=True)
    is_completed = models.BooleanField("Projeto Completo", default=False, null=True, blank=True) #se status estiver finalizado, is_completed = True
    status = models.CharField("Status do Projeto", max_length=2, choices=[("P", "Pendente"), ("CO", "Concluído"), ("EA", "Em Andamento"), ("C", "Cancelado"), ("D", "Distrato")], default="P")
    materials = models.ManyToManyField('logistics.Materials', through='logistics.ProjectMaterials', related_name='projects')
    homologator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Homologador", related_name="homologator_projects", null=True, blank=True)
    is_documentation_completed = models.BooleanField("Documentos Completos", default=False, null=True, blank=True)
    documention_completion_date = models.DateTimeField("Data de Conclusão do Documento", null=True, blank=True)
    registered_circuit_breaker = models.ForeignKey('logistics.Materials', on_delete=models.CASCADE, related_name="registered_circuit_breaker", verbose_name="Disjuntor Cadastrado", null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()

    @property
    def address(self):
        main_unit = self.units.filter(main_unit=True).first()
        return main_unit.address if main_unit else None
    
    def is_released_to_engineering(self):
        """
        Está liberado para engenharia se o projeto estiver com documentação concluída,
        pagamento completo ou parcial
        e a vistoria estiver aprovada
        """
        return self.is_documentation_completed and self.sale.payment_status in ['PG', 'PA'] and self.inspection.status == 'A'

    
    def access_opinion(self):
        """
        O parecer de acesso é liberado se:
        - O projeto tiver pelo menos um documento TRT/ART com status 'C'.
        - Todas as unidades tiverem um número de contrato (não forem nova UC).
        """
        # Verifica se existe algum documento TRT/ART com status 'C'
        has_valid_document = self.attachments.filter(
            object_id=self.id,
            content_type=ContentType.objects.get_for_model(self),
            document_type__name='TRT/ART',
            status='A'
        ).exists()
        
        # Verifica se todas as unidades têm número de contrato
        all_units_have_contract = all(unit.new_contract_number for unit in self.units.all())
        
        return has_valid_document and all_units_have_contract

    
    @property
    def attachments(self):
        return Attachment.objects.filter(
            object_id=self.id, 
            content_type=ContentType.objects.get_for_model(self)
        )

    @property
    def missing_documents(self):
        required_documents = DocumentType.objects.filter(required=True, app_label='contracts')
        missing_documents = []
        if required_documents:
            for document in required_documents:
                if not self.attachments.filter(document_type=document):
                    missing_documents.append({
                        'id': document.id,
                        'name': document.name
                    })
            return missing_documents
        return None
    
    @property
    def documents_under_analysis(self):
        return self.attachments.filter(document_type__app_label='contracts', status='Em análise')
    
    def create_deadlines(self):
        steps = Step.objects.all()
        for step in steps:
            ProjectStep.objects.create(project=self, step=step)
    
    class Meta:
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.project_number

    def save(self, current_user=None, *args, **kwargs):
        if not self.project_number:
            last_sale = Project.objects.all().order_by('id').last()
            if last_sale:
                last_number_str = last_sale.project_number.replace('PROJ', '')
                last_number = int(last_number_str) if last_number_str.isdigit() else 0
                self.project_number = f'PROJ{last_number + 1:02}'
            else:
                self.project_number = 'PROJ01'
        super().save(*args, **kwargs)
        if not self.project_steps.exists():
            self.create_deadlines()


class ProjectStep(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="project_steps")
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name="project_steps")
    deadline = models.DateField("Prazo", null=True, blank=True)
    nps = models.PositiveSmallIntegerField("NPS", null=True, blank=True)

    class Meta:
        verbose_name = "Etapa do Projeto"
        verbose_name_plural = "Etapas dos Projetos"
        unique_together = ('project', 'step')
    
    def __str__(self):
        return f"{self.project.project_number} - {self.step.name}"


    def save(self, *args, **kwargs):

        if not self.deadline and self.project.start_date:

            self.deadline = self.project.start_date + timedelta(days=self.step.default_duration_days)

        super().save(*args, **kwargs)


class ContractTemplate(models.Model):
    name = models.CharField("Nome", max_length=200)
    content = models.TextField("Conteúdo")
    is_active = models.BooleanField("Ativo", default=True)
    branches = models.ManyToManyField(Branch, verbose_name="Unidades", related_name="contract_templates")
    person_type = models.CharField("Tipo de Pessoa", max_length=1, choices=[("F", "Física"), ("J", "Jurídica")], default="F")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Modelo de Contrato"
        verbose_name_plural = "Modelos de Contrato"
        ordering = ['name']
