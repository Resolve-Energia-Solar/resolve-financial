from decimal import Decimal
from uuid import uuid4
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
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
from django.core.exceptions import ValidationError
from django.db import transaction, models
from django.db.models import Q
import datetime
from django.utils.functional import cached_property
from django.db.models import Sum


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

    # Stakeholders
    customer = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Cliente", related_name="customer_sales")
    seller = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Vendedor", related_name="seller_sales")
    sales_supervisor = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Supervisor de Vendas", related_name="supervisor_sales")
    sales_manager = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Gerente de Vendas", related_name="manager_sales")
    # Sale Information
    total_value = models.DecimalField("Valor", max_digits=20, decimal_places=3, default=0.000)
    payment_status = models.CharField("Status do Pagamento", max_length=2, choices=PAYMENT_STATUS_CHOICES, default="P")
    contract_number = models.CharField("Número do Contrato", max_length=20, unique=True, editable=False, null=True, blank=True)
    signature_date = models.DateField("Data da Assinatura", auto_now=False, auto_now_add=False, null=True, blank=True, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, verbose_name="Unidade")
    marketing_campaign = models.ForeignKey(MarketingCampaign, on_delete=models.PROTECT, verbose_name="Campanha de Marketing", null=True, blank=True)
    supplier = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Fornecedor", related_name="supplier_sales", null=True, blank=True)
    is_pre_sale = models.BooleanField("Pré-venda", default=True) 
    status = models.CharField("Status da Venda", max_length=2, choices=[("P", "Pendente"), ("F", "Finalizado"), ("EA", "Em Andamento"), ("C", "Cancelado"), ("D", "Distrato")], default="P")
    cancellation_reasons = models.ManyToManyField(Reason, verbose_name="Motivo do Cancelamento", related_name="cancellation_reason_sales", blank=True)
    billing_date = models.DateField("Data de competência", auto_now=False, auto_now_add=False, null=True, blank=True)
    attachments = GenericRelation(Attachment, related_query_name='sale_attachments')
    tags = GenericRelation('core.Tag', related_query_name='sale_tags')
    
    transfer_percentage = models.DecimalField(
        "Porcentagem de Repasse",
        max_digits=7,
        decimal_places=4,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
    )
    
    products = models.ManyToManyField('logistics.Product', through='logistics.SaleProduct', verbose_name='Produtos')

    is_completed_financial = models.BooleanField("Financeiro Completo", default=False)
    financial_completion_date = models.DateTimeField("Data de Conclusão do Financeiro", null=True, blank=True)

    # Logs
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    
    def is_released_to_engineering(self):
        return all(project.is_released_to_engineering() for project in self.projects.all())
    
    
    def final_service_opinion(self):
        final_service_opinions = []
        for project in self.projects.all():
            if project.inspection:
                final_service_opinions.append(project.inspection.final_service_opinion)
        return final_service_opinions if final_service_opinions else None
    

    def signature_status(self):
        if not self.signature_date:
            if self.contract_submissions.exists():
                if self.contract_submissions.filter(status='P').exists() and not self.contract_submissions.filter(status='A').exists():
                    return 'Enviado'
                elif self.contract_submissions.filter(status='A').exists():
                    return 'Assinado'
                elif self.contract_submissions.filter(status='R').exists():
                    return 'Recusado'
            else:
                return 'Pendente'
        return 'Assinado'
        
    @cached_property
    def total_paid(self):
        total = PaymentInstallment.objects.filter(
            payment__sale=self, 
            is_paid=True
        ).aggregate(total=Sum('installment_value'))['total']
        return total or 0

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
    
    def clean(self):
        if self.pk is not None:
            original = Sale.objects.get(pk=self.pk)
            if not original.is_pre_sale:
                # Impede a alteração do campo is_pre_sale de volta para True
                if self.is_pre_sale:
                    raise ValidationError("O campo 'Pré-venda' não pode ser alterado de volta para True após ser definido como False.")
                # Lista de campos permitidos para edição
                allowed_fields = {'seller', 'payment_status', 'marketing_campaign', 'supplier', 'status', 'is_completed_financial'}
                # Verifica se algum campo não permitido foi alterado
                for field in self._meta.fields:
                    if field.name not in allowed_fields:
                        if getattr(self, field.name) != getattr(original, field.name):
                            raise ValidationError(f"O campo '{field.verbose_name}' não pode ser editado após a pré-venda ser concluída.")
        super().clean()

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
        
    @property
    def documents_under_analysis(self):
        sale_content_type = ContentType.objects.get_for_model(Sale)
        return self.attachments.filter(content_type=sale_content_type, status='EA')
    
    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ['-created_at']
        permissions = [
            ('can_change_billing_date', 'Can change billing date'),
        ]
    
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
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, verbose_name="Venda", related_name="projects")
    product = models.ForeignKey('logistics.Product', on_delete=models.PROTECT, verbose_name="Produto", blank=True, null=True)
    project_number = models.CharField("Número do Projeto", max_length=20, null=True, blank=True)
    plant_integration = models.CharField("ID da Usina", max_length=20, null=True, blank=True)
    designer = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Projetista", related_name="designer_projects", null=True, blank=True)
    designer_status = models.CharField("Status do Projeto de Engenharia", max_length=2, choices=[("P", "Pendente"), ("CO", "Concluído"), ("EA", "Em Andamento"), ("C", "Cancelado"), ("D", "Distrato")], null=False, blank=False, default="P")
    designer_coclusion_date = models.DateField("Data de Conclusão do Projeto de Engenharia", null=True, blank=True)
    inspection = models.ForeignKey('field_services.Schedule', on_delete=models.PROTECT, verbose_name="Agendamento da Vistoria", null=True, blank=True, related_name="project_field_services")
    # ajustar quando a data de início e término for definida
    start_date = models.DateField("Data de Início", null=True, blank=True)
    end_date = models.DateField("Data de Término", null=True, blank=True)
    is_completed = models.BooleanField("Projeto Completo", default=False, null=True, blank=True) #se status estiver finalizado, is_completed = True
    status = models.CharField("Status do Projeto", max_length=2, choices=[("P", "Pendente"), ("CO", "Concluído"), ("EA", "Em Andamento"), ("C", "Cancelado"), ("D", "Distrato")], default="P")
    attachments = GenericRelation(Attachment, related_query_name='project_attachments')
    materials = models.ManyToManyField('logistics.Materials', through='logistics.ProjectMaterials', related_name='projects')
    homologator = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name="Homologador", related_name="homologator_projects", null=True, blank=True)
    is_documentation_completed = models.BooleanField("Documentos Completos", default=False, null=True, blank=True)
    material_list_is_completed = models.BooleanField("Lista de Materiais Finalizada", default=False, null=True, blank=True)
    documention_completion_date = models.DateTimeField("Data de Conclusão do Documento", null=True, blank=True)
    registered_circuit_breaker = models.ForeignKey('logistics.Materials', on_delete=models.PROTECT, related_name="registered_circuit_breaker", verbose_name="Disjuntor Cadastrado", null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()

    @property
    def address(self):
        main_unit = self.units.filter(main_unit=True).first()
        return main_unit.address if main_unit else None
    
    def is_released_to_engineering(self):
        final_service_opinion = self.inspection.final_service_opinion.name if self.inspection and self.inspection.final_service_opinion else None
        if final_service_opinion is not None:
            final_service_opinion_contains_approved = 'aprovado' in final_service_opinion.lower()
        else:
            final_service_opinion_contains_approved = False
        
        #Adicionar lógica para pegar os documentos CPF e RG estão com status aprovado
        attachments_cnh_or_rg_homologator = self.sale.attachments.filter(
            (Q(document_type__name__icontains='CNH') | 
            Q(document_type__name__icontains='RG')) &
            Q(status='A') &
            Q(document_type__name__icontains='homologador')
        )
        # attachments_cnh = self.sale.attachments.filter(document_type__name__icontains='CNH', status='A')
        # attachments_rg = self.sale.attachments.filter(document_type__name__icontains='RG', status='A')
        attachments_contract = self.sale.attachments.filter(document_type__name__icontains='Contrato', status='A')
        attachments = attachments_contract.exists() and attachments_cnh_or_rg_homologator.exists()
        
        #Check Units bill file
        main_unit = self.units.filter(main_unit=True, bill_file__isnull=False).exists()
        check_new_uc = self.units.filter(new_contract_number=True).exists()
        
        check_unit = main_unit or check_new_uc
        
        #Lógica anterior    
        # return ((self.is_documentation_completed or self.sale.status in ['F']) and self.sale.payment_status in ['L', 'C', 'CO'] and final_service_opinion_contains_approved) and not (self.status in ['CO'] and self.sale.is_pre_sale == False)
        
        return (check_unit and attachments and self.sale.payment_status in ['L', 'C', 'CO'] and final_service_opinion_contains_approved and self.sale.is_pre_sale == False and not self.status in ['C', 'D']) and self.sale.status in ['EA', 'F']
    
    
    def pending_material_list(self):
        return (self.is_released_to_engineering and not self.material_list_is_completed == True)

    
    def access_opnion(self):        
        trt_attachments = self.attachments.filter(
            Q(document_type__name__icontains='TRT') | 
            Q(document_type__name__icontains='ART'),
            object_id=self.id, 
            content_type=ContentType.objects.get_for_model(self)
        )

        new_uc_exists = self.units.filter(new_contract_number=True).exists()
        
        if trt_attachments.filter(status='A').exists() and not new_uc_exists and self.is_released_to_engineering():
            return 'Liberado'
    
        return 'Bloqueado'


    def trt_pending(self):
        trt_attachments = self.attachments.filter(
            Q(document_type__name__icontains='TRT') | 
            Q(document_type__name__icontains='ART'),
            object_id=self.id, 
            content_type=ContentType.objects.get_for_model(self)
        )
        if self.is_released_to_engineering():    
            if trt_attachments.filter(status='R').exists() and not trt_attachments.filter(status='A').exists():
                return 'Reprovada'
            if trt_attachments.filter(status='EA').exists() and not trt_attachments.filter(status='A').exists():
                return 'Em Andamento'
            if trt_attachments.filter(status='A').exists():
                return 'Concluída'
            
            return 'Pendente'
        return 'Bloqueado'


    def trt_status(self):
        trt_attachments = self.attachments.filter(
            Q(document_type__name__icontains='TRT') | 
            Q(document_type__name__icontains='ART') &
            Q(object_id=self.id, content_type=ContentType.objects.get_for_model(self))
            )
        if trt_attachments.exists() and trt_attachments.first().status and trt_attachments.count() > 1:
            return trt_attachments.first().status
        return [status for status in trt_attachments.values_list('status', flat=True)]
    
    
    def request_requested(self):
        return self.requests_energy_company.exists()
    
    # @property
    # def attachments(self):
    #     return Attachment.objects.filter(
    #         object_id=self.id, 
    #         content_type=ContentType.objects.get_for_model(self)
    #     )

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
        project_content_type = ContentType.objects.get_for_model(Project)
        return self.attachments.filter(content_type=project_content_type, status='EA')
    
    def create_deadlines(self):
        steps = Step.objects.all()
        for step in steps:
            ProjectStep.objects.create(project=self, step=step)
    
    class Meta:
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"
        ordering = ['-created_at']
        permissions = [
            ('can_change_unready_project', 'Can change unready project'),
        ]
    
    def __str__(self):
        return self.project_number

    def save(self, current_user=None, *args, **kwargs):
        if not self.project_number:
            with transaction.atomic():
                last_project = Project.objects.select_for_update().order_by('-project_number').exclude(project_number__icontains='ProjMig').first()
                last_number = 0
                
                if last_project and last_project.project_number:
                    last_number = int(last_project.project_number.replace('PROJ', ''))

                while True:
                    last_number += 1
                    new_project_number = f'PROJ{last_number:02}'
                    
                    if not Project.objects.filter(project_number=new_project_number).exists():
                        self.project_number = new_project_number
                        break
        
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
