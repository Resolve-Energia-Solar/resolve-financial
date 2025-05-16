from decimal import Decimal
from uuid import uuid4
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse_lazy
from django.utils.timezone import now
from core.models import Attachment, DocumentType
from simple_history.models import HistoricalRecords
from django.contrib.auth import get_user_model
from accounts.models import Branch
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
from django.db import transaction, models
import datetime
from django.utils.functional import cached_property
from django.db.models import Case, When, Value, CharField, Q, BooleanField, Exists, OuterRef, Subquery, Aggregate, DateField, ExpressionWrapper, F, Sum, DecimalField, Count, IntegerField, DurationField, Func, Avg, DateTimeField
from field_services.models import Schedule
from engineering.models import RequestsEnergyCompany, Units
from django.db.models.functions import TruncDate,Coalesce
from django.utils import timezone
from django.db.models.functions import Now, Cast, Round, Coalesce




def get_current_month():
    return datetime.date.today().month


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
        on_delete=models.PROTECT, 
        verbose_name="Cliente", 
        related_name="customer_leads",
        blank=True, 
        null=True
    )
    
    # CRM Information
    origin = models.ForeignKey(
        "resolve_crm.Origin", 
        on_delete=models.PROTECT, 
        verbose_name="Origem", 
        blank=True, 
        null=True
    )
    seller = models.ForeignKey(
        "accounts.User", 
        on_delete=models.PROTECT, 
        verbose_name="Vendedor", 
        related_name="lead_seller", 
        blank=True, 
        null=True
    )
    sdr = models.ForeignKey(
        "accounts.User", 
        on_delete=models.PROTECT, 
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
        on_delete=models.PROTECT, 
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
        if self.pk:
            old_lead = Lead.objects.get(pk=self.pk)
            if old_lead.column != self.column:
                self.moved_at = now()
        else:
            self.moved_at = now()

        super().save(*args, **kwargs)

        if current_user is not None:
            if not self.id:
                self.created_by = current_user
            self.updated_by = current_user
            super().save(*args, **kwargs)

        
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
    start_datetime = models.DateTimeField("Data de Início", blank=True, null=True)
    end_datetime = models.DateTimeField("Data de Término", blank=True, null=True)
    description = models.TextField("Descrição", blank=True, null=True)
    banner = models.ImageField("Banner", upload_to="resolve_crm/img/marketing_campaign/", blank=True, null=True)
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
    key_number = models.CharField("Chave do Documento", max_length=50, null=True, blank=True)
    request_signature_key = models.CharField("Chave do Signatário", max_length=50, null=True, blank=True)
    envelope_id = models.CharField("Chave do Envelope", max_length=50, null=True, blank=True)
    link = models.URLField("Link para assinatura")
    finished_at = models.DateTimeField("Finalizado em", null=True, blank=True)
    
    def __str__(self):
        return f'{self.sale.customer or "Unknown Customer"} - {self.submit_datetime or "Unknown Date"}'
    
    class Meta:
        verbose_name = "Envio de Contrato"
        verbose_name_plural = "Envios de Contrato"
        ordering = ['-submit_datetime']


class ComercialProposal(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.PROTECT, verbose_name="Lead", related_name="proposals")
    due_date = models.DateField("Prazo para aceitação", auto_now=False, auto_now_add=False)
    value = models.DecimalField("Valor da proposta", max_digits=20, decimal_places=2)
    token = models.UUIDField("Token", editable=False, default=uuid4)
    status = models.CharField("Status da proposta", max_length=1, choices=[("P", "Pendente"), ("A", "Aceita"), ("R", "Recusada")])
    observation = models.TextField("Descrição da proposta", blank=True, null=True)
    products = models.ManyToManyField('logistics.Product', through='logistics.SaleProduct', verbose_name='Produtos')

    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Criado por", related_name="created_proposals")
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    
    def __str__(self):
        return f'{self.value} - {self.lead}'
    
    class Meta:
        verbose_name = "Proposta Comercial"
        verbose_name_plural = "Propostas Comerciais"
        ordering = ['-created_at']
        

class Reason(models.Model):
    name = models.CharField("Nome", max_length=50, unique=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Motivo"
        verbose_name_plural = "Motivos"
        ordering = ["name"]
    

class Sale(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("P", "Pendente"),
        ("L", "Liberado"),
        ("C", "Concluído"),
        ("CA", "Cancelado"),
    ]

    # Stakeholders (ForeignKey já cria índice automaticamente, mas podemos reforçar com db_index se desejado)
    customer = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Cliente", related_name="customer_sales")
    seller = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Vendedor", related_name="seller_sales")
    sales_supervisor = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Supervisor de Vendas", related_name="supervisor_sales")
    sales_manager = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Gerente de Vendas", related_name="manager_sales")
    
    # Sale Information
    total_value = models.DecimalField("Valor", max_digits=20, decimal_places=3, default=0.000)
    payment_status = models.CharField("Status do Pagamento", max_length=2, choices=PAYMENT_STATUS_CHOICES, default="P", db_index=True)
    contract_number = models.CharField("Número do Contrato", max_length=20, unique=True, editable=False, null=True, blank=True)
    signature_date = models.DateTimeField("Data da Assinatura", auto_now=False, auto_now_add=False, null=True, blank=True, db_index=True)
    branch = models.ForeignKey('accounts.Branch', on_delete=models.PROTECT, verbose_name="Unidade", db_index=True)
    marketing_campaign = models.ForeignKey('MarketingCampaign', on_delete=models.PROTECT, verbose_name="Campanha de Marketing", null=True, blank=True)
    supplier = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Fornecedor", related_name="supplier_sales", null=True, blank=True)
    is_pre_sale = models.BooleanField("Pré-venda", default=True, db_index=True) 
    status = models.CharField(
        "Status da Venda", 
        max_length=2, 
        choices=[
            ("P", "Pendente"), 
            ("F", "Finalizado"), 
            ("EA", "Em Andamento"), 
            ("C", "Cancelado"), 
            ("D", "Distrato")
        ], 
        default="P",
        db_index=True
    )
    cancellation_reasons = models.ManyToManyField('Reason', verbose_name="Motivo do Cancelamento", related_name="cancellation_reason_sales", blank=True)
    billing_date = models.DateField("Data de competência", auto_now=False, auto_now_add=False, null=True, blank=True, db_index=True)
    attachments = GenericRelation('core.Attachment', related_query_name='sale_attachments')
    tags = GenericRelation('core.Tag', related_query_name='sale_tags')
    reference_table = models.CharField("Tabela de Referência", max_length=100, null=True, blank=True)
    transfer_percentage = models.DecimalField(
        "Porcentagem de Repasse",
        max_digits=7,
        decimal_places=4,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
    )
    
    products = models.ManyToManyField('logistics.Product', through='logistics.SaleProduct', verbose_name='Produtos')

    is_completed_financial = models.BooleanField("Financeiro Completo", default=False, db_index=True)
    financial_completion_date = models.DateTimeField("Data de Conclusão do Financeiro", null=True, blank=True, db_index=True)

    # Logs
    created_at = models.DateTimeField("Criado em", auto_now_add=True, db_index=True)
    history = HistoricalRecords()
    
    
    def calculate_franchise_installment_value(self, reference_value: Decimal) -> Decimal:
        if reference_value is None:
            reference_value = Decimal("0.00")

        total_value = self.total_value or Decimal("0.00")
        difference = total_value - reference_value

        transfer_percentage = self.transfer_percentage or (
            self.branch.transfer_percentage if self.branch else Decimal("0.00")
        )
        
        margin_percentage = self.branch.margin or Decimal("0.00")
        margin = max(difference * (margin_percentage / Decimal("100")), Decimal("0.00"))
        
        transfer_percentage = Decimal(transfer_percentage) / Decimal("100")

        marketing_tax = self.branch.marketing_tax or Decimal("0.00")
        marketing_tax_value = total_value * (marketing_tax / Decimal("100"))
        
        print(f"marketing_tax_value: {marketing_tax_value}")

        if difference <= 0:
            installment_value = reference_value * transfer_percentage - margin - marketing_tax_value - abs(difference)
        else:
            installment_value = (
                reference_value * transfer_percentage
                - margin
                + difference
                - marketing_tax_value
            )

        return round(max(installment_value, Decimal("0.00")), 6)


    def user_can_edit(self, user):
        if self.is_pre_sale or self.status in ['P', 'EA']:
            return True
        return user.has_perm('resolve_crm.can_change_fineshed_sale')


    @property
    def franchise_installments_generated(self):
        return self.franchise_installments.exists()
    
    def treadmill_counter(self):
        if not self.signature_date:
            return None

        from django.db.models import Prefetch
        from field_services.models import Schedule
        from django.utils.timezone import now

        qs = self.projects.all().prefetch_related(
            Prefetch(
                'field_services',
                queryset=Schedule.objects.filter(
                    service__category__name='Instalação',
                    final_service_opinion__name='Concluído'
                ).select_related('service', 'final_service_opinion'),
                to_attr='installations_filtered'
            )
        )

        counters = {}
        for project in qs:
            if project.installations_filtered:
                installation = project.installations_filtered[0]
                if installation.execution_finished_at:
                    days = (installation.execution_finished_at - self.signature_date).days
                else:
                    days = (now() - self.signature_date).days
            else:
                days = (now() - self.signature_date).days
            counters[project.id] = days

        unique_days = set(counters.values())
        if len(unique_days) == 1:
            return unique_days.pop()
        else:
            return counters
    
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
    
    # def clean(self):
    #     if self.pk is not None:
    #         original = Sale.objects.get(pk=self.pk)
    #         if not original.is_pre_sale:
    #             if self.is_pre_sale:
    #                 raise ValidationError("O campo 'Pré-venda' não pode ser alterado de volta para True após ser definido como False.")
    #             allowed_fields = {'seller', 'payment_status', 'marketing_campaign', 'supplier', 'status', 'is_completed_financial'}
    #             for field in self._meta.fields:
    #                 if field.name not in allowed_fields:
    #                     if getattr(self, field.name) != getattr(original, field.name):
    #                         raise ValidationError(f"O campo '{field.verbose_name}' não pode ser editado após a pré-venda ser concluída.")
    #     super().clean()

    def save(self, *args, **kwargs):
        if not self.contract_number:
            with transaction.atomic():
                last_sale = Sale.objects.select_for_update().order_by('-contract_number').first()
                last_number = 0
                if last_sale and last_sale.contract_number:
                    last_number = int(last_sale.contract_number.replace('RESOL', ''))
                while True:
                    last_number += 1
                    new_contract_number = f'RESOL{last_number:02}'
                    if not Sale.objects.filter(contract_number=new_contract_number).exists():
                        self.contract_number = new_contract_number
                        break
        if not self.billing_date and self.signature_date:
            self.billing_date = self.signature_date
        if (self.payment_status == 'C' or self.payment_status == 'L') and not self.financial_completion_date:
            self.financial_completion_date = now()
            self.is_completed_financial = True
        if (self.payment_status == 'P' or self.payment_status == 'CA') and self.financial_completion_date:
            self.financial_completion_date = None
            self.is_completed_financial = False
        super().save(*args, **kwargs)
    
    
    
    """
    def clean(self):
        if self.is_pre_sale:
            qs = Sale.objects.filter(customer=self.customer, is_pre_sale=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Já existe uma pré-venda para esse cliente.")
        super().clean()
    """
    
    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_status']),
            models.Index(fields=['status']),
            models.Index(fields=['billing_date']),
            models.Index(fields=['created_at']),
            models.Index(fields=['branch']),
            models.Index(fields=['is_pre_sale']),
            models.Index(fields=['is_completed_financial']),
            models.Index(fields=['financial_completion_date']),
            models.Index(fields=['contract_number']),
            models.Index(fields=['branch', 'payment_status']),
            models.Index(fields=['is_pre_sale', 'payment_status']),
        ]
        permissions = [
            ('can_change_billing_date', 'Can change billing date'),
            ('can_change_fineshed_sale', 'Can change finished sale'),
        ]
        """
        constraints = [
            models.UniqueConstraint(
                fields=['customer'],
                condition=models.Q(is_pre_sale=True),
                name='unique_pre_sale_per_customer'
            )
        ]
        """
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


class GroupConcat(Aggregate):
    function = 'GROUP_CONCAT'
    template = "%(function)s(%(distinct)s%(expressions)s SEPARATOR '%(separator)s')"
    allow_distinct = True

    def __init__(self, expression, distinct=False, separator=', ', **extra):
        super().__init__(
            expression,
            distinct='DISTINCT ' if distinct else '',
            separator=separator,
            output_field=CharField(),
            **extra
        )
        

class TimestampDiff(Func):
    function = 'TIMESTAMPDIFF'
    template = "%(function)s(DAY, %(expressions)s)"
    output_field = IntegerField()
    

class ProjectQuerySet(models.QuerySet):
    def with_is_released_to_engineering(self):
        sale_ct = ContentType.objects.get_for_model(Sale)

        has_contract = Exists(
            Attachment.objects.filter(
                content_type=sale_ct,
                object_id=OuterRef('sale_id'),
                status='A',
                document_type__name__icontains='Contrato'
            ).values('id')  # Adicionando .values('id') para garantir que só um valor seja retornado
        )

        # Subconsulta para verificar se há CNH ou RG do homologador
        has_cnh_or_rg_homologador = Exists(
            Attachment.objects.filter(
                content_type=sale_ct,
                object_id=OuterRef('sale_id'),
                status='A'
            ).filter(
                Q(document_type__name__icontains='CNH') | Q(document_type__name__icontains='RG'),
                document_type__name__icontains='homologador'
            ).values('id')  # Limita a subconsulta para retornar apenas 'id'
        )

        # Restante das subconsultas
        has_unit_with_bill_file = Exists(
            Units.objects.filter(
                project=OuterRef('pk'),
                bill_file__isnull=False
            ).values('id')  # Limita a subconsulta para retornar apenas 'id'
        )

        has_new_contract_uc = Exists(
            Units.objects.filter(
                project=OuterRef('pk'),
                new_contract_number=True
            ).values('id')  # Limita a subconsulta para retornar apenas 'id'
        )

        return self.annotate(
            is_released_to_engineering=Case(
                When(
                    Q(sale__payment_status__in=['L', 'C', 'CO']) &
                    Q(inspection__final_service_opinion__name__icontains='Aprovado') &
                    Q(sale__is_pre_sale=False) &
                    ~Q(status__in=['C', 'D']) &
                    Q(sale__status__in=['EA', 'F']) &
                    has_contract &
                    has_cnh_or_rg_homologador &
                    (has_unit_with_bill_file | has_new_contract_uc),
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField(),
            )
        ).distinct()


    def with_trt_status(self):
        from core.models import Attachment 
        from django.contrib.contenttypes.models import ContentType

        project_content_type = ContentType.objects.get_for_model(Project)

        return self.annotate(
            trt_status=Subquery(
                Attachment.objects.filter(
                    object_id=OuterRef('pk'),
                    content_type=project_content_type,
                    document_type__name='ART/TRT'
                ).order_by('-created_at').values('status')[:1],
                output_field=CharField()
            )
        ).distinct()


    def with_pending_material_list(self):
        return self.with_is_released_to_engineering().annotate(
            pending_material_list=Case(
                When(
                    Q(is_released_to_engineering=True)
                    & Q(material_list_is_completed=False),
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField(),
            )
        ).distinct()


    def with_access_opnion(self):
        return self.with_trt_status().with_is_released_to_engineering().annotate(
            access_opnion=Case(
                When(
                    Q(trt_status='A')
                    & ~Q(units__new_contract_number=True)
                    & Q(is_released_to_engineering=True),
                    then=Value('Liberado')
                ),
                default=Value('Bloqueado'),
                output_field=CharField(),
            )
        ).distinct()


    def with_trt_pending(self):
        return self.with_is_released_to_engineering().with_trt_status().annotate(
            trt_pending=Case(
                When(Q(is_released_to_engineering=False), then=Value('Bloqueado')),
                When(Q(trt_status='R') & ~Q(trt_status='A'), then=Value('Reprovada')),
                When(Q(trt_status='EA') & ~Q(trt_status='A'), then=Value('Em Andamento')),
                When(Q(trt_status='A'), then=Value('Concluída')),
                default=Value('Pendente'),
                output_field=CharField(),
            )
        ).distinct()


    def with_request_requested(self):
        return self.annotate(
            request_requested=Case(
                When(Q(requests_energy_company__isnull=False), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )


    def with_last_installation_final_service_opinion(self):
        return self.annotate(
            last_installation_final_service_opinion=Subquery(
                Schedule.objects.filter(
                    project=OuterRef('pk'),
                    service__category__name__icontains='Instalação'
                ).order_by('-created_at').values('final_service_opinion__name')[:1],
                output_field=CharField()
            )
        ).distinct()
        
        
    def with_request_days_since_requested(self, type_name: str, annotation_name: str):
        base_qs = RequestsEnergyCompany.objects.filter(
            project=OuterRef('pk'),
            type__name__icontains=type_name
        ).order_by('-request_date')

        request_date_subquery = base_qs.values('request_date')[:1]
        conclusion_date_subquery = base_qs.values('conclusion_date')[:1]

        return self.annotate(
            **{
                f"{annotation_name}_int": TimestampDiff(
                    Subquery(request_date_subquery),
                    Coalesce(Subquery(conclusion_date_subquery), Func(function='NOW'))
                )
            }
        )


    def with_supply_adquance_names(self):
        subquery = Units.objects.filter(
            project=OuterRef('pk'),
            main_unit=True,
            supply_adquance__isnull=False
        ).values_list('supply_adquance__name', flat=True)

        return self.annotate(
            supply_adquance_names=Coalesce(Subquery(
                Units.objects
                .filter(
                    project=OuterRef('pk'),
                    main_unit=True,
                    supply_adquance__isnull=False
                )
                .order_by()
                .annotate(names_concat=GroupConcat('supply_adquance__name'))
                .values('names_concat')[:1]
            ), Value(''))
        ).distinct()

    # PARECER DE ACESSO
    def with_access_opnion_status(self):
        return self.with_access_opnion().with_last_installation_final_service_opinion().with_request_days_since_requested('Parecer de Acesso', 'access_opnion_days').annotate(
            access_opnion_status=Case(
                When(Q(is_released_to_engineering=False), then=Value('Bloqueado')),
                When(
                    # Q(last_installation_final_service_opinion__iexact='Concluído') &
                    Q(access_opnion='Liberado') &
                    Q(requests_energy_company__isnull=True),
                    then=Value('Pendente'),
                ),
                When(
                    # Q(last_installation_final_service_opinion__iexact='Concluído') &
                    Q(access_opnion='Liberado') &
                    Q(requests_energy_company__isnull=False) &
                    ~Q(requests_energy_company__type__name__icontains='Parecer de Acesso'),
                    then=Value('Pendente')
                ),
                When(
                    # Q(last_installation_final_service_opinion__iexact='Concluído') &
                    Q(access_opnion='Liberado') &
                    Q(requests_energy_company__type__name__icontains='Parecer de Acesso', requests_energy_company__status='S'),
                    then=Value('Solicitado')
                ),
                When(
                    # Q(last_installation_final_service_opinion__iexact='Concluído') &
                    Q(access_opnion='Liberado') &
                    Q(requests_energy_company__type__name__icontains='Parecer de Acesso', requests_energy_company__status='D'),
                    then=Value('Deferido')
                ),
                When(
                    # Q(last_installation_final_service_opinion__iexact='Concluído') &
                    Q(access_opnion='Liberado') &
                    Q(requests_energy_company__type__name__icontains='Parecer de Acesso', requests_energy_company__status='I'),
                    then=Value('Indeferida')
                ),
                default=Value('Bloqueado'),
                output_field=CharField(),
            )
        ).distinct()


    # AUMENTO DE CARGA
    def with_load_increase_status(self):
        return self.with_is_released_to_engineering().with_supply_adquance_names().with_last_installation_final_service_opinion().with_request_days_since_requested('Aumento de Carga', 'load_increase_days').annotate(
            load_increase_status=Case(
                When(~Q(supply_adquance_names__icontains='Aumento de Carga'), then=Value('Não se aplica')),
                When(
                    Q(supply_adquance_names__icontains='Aumento de Carga') &
                    ~Q(last_installation_final_service_opinion__iexact='Concluído'),
                    then=Value('Bloqueado')
                ),
                When(
                    Q(supply_adquance_names__icontains='Aumento de Carga')
                    & Q(last_installation_final_service_opinion__iexact='Concluído')
                    & Q(requests_energy_company__isnull=True),
                    then=Value('Pendente')
                ),
                When(
                    Q(supply_adquance_names__icontains='Aumento de Carga') &
                    Q(requests_energy_company__isnull=False) &
                    ~Q(requests_energy_company__type__name__icontains='Aumento de Carga'),
                    then=Value('Pendente')
                ),
                
                When(Q(supply_adquance_names__icontains='Aumento de Carga') &
                     Q(requests_energy_company__status='S') &
                     Q(requests_energy_company__type__name__icontains='Aumento de Carga')
                      , then=Value('Solicitado')),
                When(Q(supply_adquance_names__icontains='Aumento de Carga') &
                     Q(requests_energy_company__status='D') &
                     Q(requests_energy_company__type__name__icontains='Aumento de Carga')
                     , then=Value('Deferido')),
                When(Q(supply_adquance_names__icontains='Aumento de Carga') &
                     Q(requests_energy_company__status='I') & 
                     Q(requests_energy_company__type__name__icontains='Aumento de Carga')
                     , then=Value('Indeferida')),
                default=Value('Bloqueado'),
                output_field=CharField(),
            )
        ).distinct()


    # AJUSTE DE RAMAL
    def with_branch_adjustment_status(self):
        return (
            self.with_is_released_to_engineering()
                .with_supply_adquance_names()
                .with_last_installation_final_service_opinion()
                .with_request_days_since_requested('Ajuste de Ramal', 'branch_adjustment_days')
                .annotate(
                    branch_adjustment_status=Case(
                        When(~Q(supply_adquance_names__icontains='Ajuste de Ramal'), then=Value('Não se aplica')),
                        When(
                            Q(supply_adquance_names__icontains='Ajuste de Ramal') & 
                            ~Q(last_installation_final_service_opinion__iexact='Concluído'),
                            then=Value('Bloqueado')
                        ),
                        When(
                            Q(supply_adquance_names__icontains='Ajuste de Ramal')
                            & Q(last_installation_final_service_opinion__iexact='Concluído')
                            & Q(requests_energy_company__isnull=True),
                            then=Value('Pendente')
                        ),
                        
                        When(Q(supply_adquance_names__icontains='Ajuste de Ramal') &
                                Q(requests_energy_company__isnull=False) &
                                ~Q(requests_energy_company__type__name__icontains='Ajuste de Ramal')
                                , then=Value('Pendente')),
                        
                        When(Q(supply_adquance_names__icontains='Ajuste de Ramal') &
                             Q(requests_energy_company__status='S') &
                             Q(requests_energy_company__type__name__icontains='Ajuste de Ramal')
                             , then=Value('Solicitado')),
                        When(Q(supply_adquance_names__icontains='Ajuste de Ramal') & 
                             Q(requests_energy_company__status='D') & 
                             Q(requests_energy_company__type__name__icontains='Ajuste de Ramal')
                             , then=Value('Deferido')),
                        When(Q(supply_adquance_names__icontains='Ajuste de Ramal') &
                             Q(requests_energy_company__status='I') & 
                             Q(requests_energy_company__type__name__icontains='Ajuste de Ramal')
                             , then=Value('Indeferida')),
                        default=Value('Bloqueado'),
                        output_field=CharField(),
                    )
                ).distinct()
        )


    # NOVA UC
    def with_new_contact_number_status(self):
        main_unit_has_new_contract = Units.objects.filter(
            project=OuterRef('pk'),
            main_unit=True,
            new_contract_number=True
        )

        return (
            self.with_is_released_to_engineering()
            .with_request_days_since_requested('Nova UC', 'new_contact_number_days')
            .annotate(
                has_main_unit_new_contract=Exists(main_unit_has_new_contract)
            )
            .annotate(
                new_contact_number_status=Case(
                    When(
                        has_main_unit_new_contract=False,
                        then=Value('Não se aplica')
                    ),
                    When(
                        has_main_unit_new_contract=True,
                        then=Case(
                            When(is_released_to_engineering=False, then=Value('Bloqueado')),
                            When(~Q(designer_status='CO'), then=Value('Bloqueado')),
                            When(
                                Q(requests_energy_company__isnull=True) &
                                Q(requests_energy_company__type__name__icontains='Nova UC'),
                                then=Value('Pendente')
                            ),
                            When(
                                Q(requests_energy_company__isnull=False) &
                                ~Q(requests_energy_company__type__name__icontains='Nova UC'),
                                then=Value('Pendente')
                            ),
                            When(
                                Q(requests_energy_company__status='S') &
                                Q(requests_energy_company__type__name__icontains='Nova UC'),
                                then=Value('Solicitado')
                            ),
                            When(
                                Q(requests_energy_company__status='D') &
                                Q(requests_energy_company__type__name__icontains='Nova UC'),
                                then=Value('Deferido')
                            ),
                            When(
                                Q(requests_energy_company__status='I') &
                                Q(requests_energy_company__type__name__icontains='Nova UC'),
                                then=Value('Indeferida')
                            ),
                            default=Value('Bloqueado')
                        )
                    )
                )
            )
        )


    # VISTORIA FINAL
    # instalacao completa
    # parecer de acesso concluido
    # se nao precisa de adequacao de fornecimento liberado
    
    def with_final_inspection_status(self):
        return self.with_is_released_to_engineering().with_request_days_since_requested('Vistoria Final', 'final_inspection_days').annotate(
            final_inspection_status=Case(
                When(Q(is_released_to_engineering=False), then=Value('Bloqueado')),
                When(
                    Q(is_released_to_engineering=True)
                    & ~Q(requests_energy_company__type__name__icontains='Parecer de Acesso', requests_energy_company__status='S'),
                    then=Value('Bloqueado')
                ),
                When(
                    Q(requests_energy_company__type__name__icontains='Parecer de Acesso', requests_energy_company__status='D')
                    & Q(last_installation_final_service_opinion__iexact='Concluído')
                    & ~Q(requests_energy_company__type__name__icontains='Vistoria Final'),
                    then=Value('Pendente')
                ),
                When(Q(requests_energy_company__type__name__icontains='Vistoria Final',
                    requests_energy_company__status='S'), then=Value('Solicitado')),
                When(Q(requests_energy_company__type__name__icontains='Vistoria Final', requests_energy_company__status='D'), then=Value('Deferido')),
                When(Q(requests_energy_company__type__name__icontains='Vistoria Final', requests_energy_company__status='I'), then=Value('Indeferida')),
                default=Value('Bloqueado'),
                output_field=CharField(),
            )
        ).distinct()


    # STATUS LOGISTICA -  PERGUNTAR - QUANDO NÃO É ENTREGA DIRETA O STATUS DE LIBERADO DEPENDE DA ENTREGA?
    def with_delivery_status(self):
        return self.with_is_released_to_engineering().annotate(
            # Subquery para pegar o nome do parecer final do último agendamento
            last_service_opinion_name=Subquery(
                Schedule.objects.filter(
                    project=OuterRef('pk'),  # Refere-se ao projeto atual
                    service__name__icontains='Entrega',  # Serviço com nome contendo 'Entrega'
                ).order_by('-created_at').values('final_service_opinion__name')[:1], 
            ),
            has_delivery=Exists(
                Schedule.objects.filter(
                    project=OuterRef('pk'),
                    service__name__icontains='Entrega'
                ).values('id')
            ),
            delivery_status=Case(
                # CASO NÃO ESTEJA LIBERADO PARA ENGENHARIA
                When(Q(is_released_to_engineering=False), then=Value('Bloqueado')),

                # CASO NÃO TENHA COMPRA
                When(Q(purchases__isnull=True), then=Value('Bloqueado')),

                # CONDIÇÕES PARA "BLOQUEADO"
                When(
                    Q(purchases__isnull=False) &
                    (
                        # ENTREGA DIRETA E NÃO ESTÁ COM O STATUS 'COMPRA REALIZADA (R)'
                        (Q(purchases__delivery_type='D') & ~Q(purchases__status='R')) |
                        # ENTREGA CD E NÃO ESTÁ COM O STATUS 'COMPRA REALIZADA (R)' E LISTA DE MATERIAIS NÃO FINALIZADA
                        (Q(purchases__delivery_type='C') & ~Q(purchases__status='R') & ~Q(material_list_is_completed=True)) |
                        # ENTREGA CD E STATUS 'COMPRA REALIZADA (R)' E STATUS DO PROJETO NÃO 'CO' E LISTA DE MATERIAIS NÃO FINALIZADA
                        (Q(purchases__delivery_type='C') & Q(purchases__status='R') & ~Q(designer_status__in=['CO']) & ~Q(material_list_is_completed=True))
                    ),
                    then=Value('Bloqueado')
                ),

                # CASO ENTREGA DIRETA E STATUS 'COMPRA REALIZADA (R)'
                When(
                    Q(purchases__isnull=False) &
                    Q(purchases__delivery_type='D') &
                    Q(purchases__status='R') &
                    Q(has_delivery=False),
                    then=Value('Liberado')
                ),

                # CASO ENTREGA CD COM STATUS 'COMPRA REALIZADA (R)' E STATUS DO PROJETO 'CO' E LISTA DE MATERIAIS FINALIZADA
                When(
                    Q(purchases__isnull=False) &
                    Q(purchases__delivery_type='C') &
                    Q(purchases__status='R') &
                    Q(designer_status__in=['CO']) &
                    Q(material_list_is_completed=True) &
                    Q(has_delivery=False),
                    then=Value('Liberado')
                ),

                # AGENDADO: Verifica se o último agendamento com serviço contendo 'Entrega' existe
                When(
                    Q(last_service_opinion_name__isnull=True),
                    then=Value('Agendado')
                ),

                # ENTREGUE: Verifica o parecer final do último agendamento com serviço contendo 'Entrega' e com parecer final 'Entregue'
                When(
                    Q(last_service_opinion_name__icontains='Entregue'),
                    then=Value('Entregue')
                ),

                # CANCELADO: Verifica o parecer final do último agendamento com serviço contendo 'Entrega' e com parecer final 'Cancelado'
                When(
                    Q(last_service_opinion_name__icontains='Cancelado'),
                    then=Value('Cancelado')
                ),

                # Caso padrão
                default=Value('Bloqueado'),
                output_field=CharField(),
            )
        ).distinct()
        
        
    def with_purchase_status(self):
        return self.with_is_released_to_engineering().annotate(
            purchase_status=Case(
                When(Q(is_released_to_engineering=False), then=Value('Bloqueado')),
                When(Q(purchases__isnull=True), then=Value('Liberado')),
                When(Q(purchases__status='P'), then=Value('Pendente')),
                When(Q(purchases__status='R'), then=Value('Compra Realizada')),
                When(Q(purchases__status='C'), then=Value('Cancelado')),
                When(Q(purchases__status='D'), then=Value('Distrato')),
                When(Q(purchases__status='F'), then=Value('Aguardando Previsão de Entrega')),
                When(Q(purchases__status='A'), then=Value('Aguardando Pagamento')),
                default=Value('Bloqueado'),
                output_field=CharField(),
            )
        ).distinct()
        

    def with_expected_delivery_date(self):
        return self.annotate(
            expected_delivery_date=Case(
                When(
                    sale__signature_date__isnull=False,
                    then=Cast(
                        ExpressionWrapper(
                            F('sale__signature_date') + timedelta(days=20),
                            output_field=DateField()
                        ),
                        output_field=DateField()
                    )
                ),
                default=None,
                output_field=DateField()
            ),
            expected_delivery_status=Case(
                When(sale__signature_date__isnull=True, then=Value('Sem contrato')),
                default=Value('Com contrato'),
                output_field=CharField()
            )
        )

    
    # FINANCEIRO
    def with_installments_indicators(self):
        now = timezone.now()

        return self.annotate(
            overdue_installments_count=Count(
                'sale__payments__installments',
                filter=Q(
                    sale__payments__installments__is_paid=False,
                    sale__payments__installments__due_date__lte=now
                ),
                distinct=True
            ),
            overdue_installments_value=Coalesce(
                Sum(
                    'sale__payments__installments__installment_value',
                    filter=Q(
                        sale__payments__installments__is_paid=False,
                        sale__payments__installments__due_date__lte=now
                    ),
                    output_field=DecimalField()
                ),
                Value(0)
            ),
            on_time_installments_count=Count(
                'sale__payments__installments',
                filter=Q(
                    sale__payments__installments__is_paid=False,
                    sale__payments__installments__due_date__gt=now
                ),
                distinct=True
            ),
            on_time_installments_value=Coalesce(
                Sum(
                    'sale__payments__installments__installment_value',
                    filter=Q(
                        sale__payments__installments__is_paid=False,
                        sale__payments__installments__due_date__gt=now
                    ),
                    output_field=DecimalField()
                ),
                Value(0)
            ),
            paid_installments_count=Count(
                'sale__payments__installments',
                filter=Q(sale__payments__installments__is_paid=True),
                distinct=True
            ),
            paid_installments_value=Coalesce(
                Sum(
                    'sale__payments__installments__installment_value',
                    filter=Q(sale__payments__installments__is_paid=True),
                    output_field=DecimalField()
                ),
                Value(0)
            ),
            total_installments=Count(
                'sale__payments__installments',
                distinct=True
            ),
            total_installments_value=Coalesce(
                Sum(
                    'sale__payments__installments__installment_value',
                    output_field=DecimalField()
                ),
                Value(0)
            )
        )

    def with_status_annotations(self):
        return (
            self
            # default
            .with_is_released_to_engineering()
            .with_pending_material_list()
            # Homologation
            .with_access_opnion()
            .with_request_requested()
            .with_last_installation_final_service_opinion()
            .with_supply_adquance_names()
            .with_access_opnion_status()
            .with_load_increase_status()
            .with_branch_adjustment_status()
            .with_new_contact_number_status()
            .with_final_inspection_status()
            .with_trt_pending()
            # Logistics
            .with_delivery_status()
            .with_purchase_status()
            .with_expected_delivery_date()
        ).distinct()


    def with_avg_time_installation(self):
        entrega_finished_at_subquery = Schedule.objects.filter(
            project=OuterRef('pk'),
            service__name__icontains='entrega',
            execution_finished_at__isnull=False,
        ).order_by('-execution_finished_at').values('execution_finished_at')[:1]

        installation_schedules = Schedule.objects.filter(
            project=OuterRef('pk'),
            service__name__icontains='instalação',
            execution_started_at__isnull=False,
            execution_finished_at__isnull=False,
        ).annotate(
            entrega_finished_at=Subquery(entrega_finished_at_subquery, output_field=DateTimeField())
        ).annotate(
            duration=ExpressionWrapper(
                F('execution_finished_at') - F('entrega_finished_at'),
                output_field=DurationField()
            )
        ).values('project').annotate(
            avg_duration=Avg('duration')
        ).values('avg_duration')[:1]

        return self.annotate(
            avg_time_installation=Subquery(installation_schedules, output_field=DurationField())
        )


    def with_customer_released_flag(self):
        inspection_done = Schedule.objects.filter(
            project=OuterRef("pk"),
            service__name__icontains="vistoria",
            agent_status="C",
        )

        delivery_done = Schedule.objects.filter(
            project=OuterRef("pk"),
            service__name__icontains="entrega",
            agent_status="C",
        )

        return self.annotate(
            customer_released=Exists(inspection_done) & Exists(delivery_done)
        )

    def with_number_of_installations(self):
        return self.annotate(
            number_of_installations=Count(
                'field_services',
                filter=Q(
                    field_services__service__name__icontains='instalação',
                    field_services__execution_finished_at__isnull=False,
                    field_services__schedule_date__isnull=False
                ),
                distinct=True
            )
        )



class Project(models.Model):
    sale = models.ForeignKey('resolve_crm.Sale', on_delete=models.PROTECT, verbose_name="Venda", related_name="projects")
    product = models.ForeignKey('logistics.Product', on_delete=models.PROTECT, verbose_name="Produto", blank=True, null=True)
    project_number = models.CharField("Número do Projeto", max_length=20, null=True, blank=True)
    plant_integration = models.CharField("ID da Usina", max_length=20, null=True, blank=True)
    designer = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Projetista", related_name="designer_projects", null=True, blank=True)
    designer_status = models.CharField(
        "Status do Projeto de Engenharia",
        max_length=2,
        choices=[
            ("P", "Pendente"),
            ("CO", "Concluído"),
            ("EA", "Em Andamento"),
            ("C", "Cancelado"),
            ("D", "Distrato")
        ],
        default="P"
    )
    designer_coclusion_date = models.DateField("Data de Conclusão do Projeto de Engenharia", null=True, blank=True)
    inspection = models.ForeignKey(
        'field_services.Schedule',
        on_delete=models.PROTECT,
        verbose_name="Agendamento da Vistoria",
        null=True,
        blank=True,
        related_name="project_field_services"
    )
    start_date = models.DateField("Data de Início", null=True, blank=True)
    end_date = models.DateField("Data de Término", null=True, blank=True)
    is_completed = models.BooleanField("Projeto Completo", default=False, null=True, blank=True)
    status = models.CharField(
        "Status do Projeto",
        max_length=2,
        choices=[
            ("P", "Pendente"),
            ("CO", "Concluído"),
            ("EA", "Em Andamento"),
            ("C", "Cancelado"),
            ("D", "Distrato")
        ],
        default="P"
    )
    # Utilize a referência em string caso Attachment esteja em outro app, por exemplo, 'core.Attachment'
    attachments = GenericRelation('core.Attachment', related_query_name='project_attachments')
    processes = GenericRelation('core.Process', related_query_name='project_processes')
    materials = models.ManyToManyField('logistics.Materials', through='logistics.ProjectMaterials', related_name='projects')
    homologator = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Homologador", related_name="homologator_projects", null=True, blank=True)
    is_documentation_completed = models.BooleanField("Documentos Completos", default=False, null=True, blank=True)
    material_list_is_completed = models.BooleanField("Lista de Materiais Finalizada", default=False, null=True, blank=True)
    documention_completion_date = models.DateTimeField("Data de Conclusão do Documento", null=True, blank=True)
    registered_circuit_breaker = models.ForeignKey(
        'logistics.Materials',
        on_delete=models.PROTECT,
        related_name="registered_circuit_breaker",
        verbose_name="Disjuntor Cadastrado",
        null=True,
        blank=True
    )
    objects = ProjectQuerySet.as_manager()
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()

    @cached_property
    def address(self):
        main_unit = self.units.filter(main_unit=True).first()
        return main_unit.address if main_unit else None
    
    @cached_property
    def documents_under_analysis(self):
        return [
            att for att in self.attachments.all()
            if att.content_type_id == self.content_type_id and att.status == 'EA'
        ]
    
    # @property
    # def missing_documents(self):
    #     required_documents = DocumentType.objects.filter(required=True, app_label='contracts')
    #     missing_documents = []
    #     if required_documents:
    #         for document in required_documents:
    #             if not self.attachments.filter(document_type=document).exists():
    #                 missing_documents.append({
    #                     'id': document.id,
    #                     'name': document.name
    #                 })
    #         return missing_documents
    #     return None
    
    def create_deadlines(self):
        steps = Step.objects.all()
        for step in steps:
            ProjectStep.objects.create(project=self, step=step)
    
    class Meta:
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project_number']),
            models.Index(fields=['status']),
            models.Index(fields=['designer_status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['is_completed']),
            models.Index(fields=['is_documentation_completed']),
            models.Index(fields=['material_list_is_completed']),
            models.Index(fields=['documention_completion_date']),
            models.Index(fields=['created_at']),
            models.Index(fields=['sale']),
            models.Index(fields=['sale', 'status']),
        ]
        permissions = [
            ('can_change_unready_project', 'Can change unready project'),
            ('can_view_journey', 'Can view journey'),
            ('can_manage_journey', 'Can manage journey'),
        ]
    
    def __str__(self):
        return self.project_number if self.project_number else f'Projeto {self.id}'

    def save(self, current_user=None, *args, **kwargs):
        if self.is_documentation_completed and not self.documention_completion_date:
            self.documention_completion_date = now()
        if not self.designer_coclusion_date and self.designer_status == 'CO':
            self.designer_coclusion_date = now()
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
