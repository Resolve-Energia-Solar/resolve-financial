from django.db import models
from django.urls import reverse_lazy
from simple_history.models import HistoricalRecords
from django.contrib.auth import get_user_model
from accounts.models import Branch


class Lead(models.Model):

    # Personal Information
    name = models.CharField(max_length=200, verbose_name="Nome")
    type = models.CharField(max_length=200, verbose_name="Tipo", help_text="Pessoa Física ou Jurídica?", choices=[("PF", "Pessoa Física"), ("PJ", "Pessoa Jurídica")])
    byname = models.CharField(max_length=200, verbose_name="Apelido", blank=True, null=True)

    # Lead
    contact_email = models.EmailField(verbose_name="E-mail")
    phone = models.CharField(max_length=20, verbose_name="Telefone")
    address = models.ForeignKey("accounts.Address", on_delete=models.CASCADE, verbose_name="Endereço", blank=True, null=True)
    customer = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Cliente", related_name="customer_leads", blank=True, null=True)
    
    # CRM Information
    origin = models.CharField(max_length=200, verbose_name="Origem", blank=True, null=True)
    seller = models.ForeignKey("accounts.User", on_delete=models.CASCADE, verbose_name="Vendedor", related_name="lead_seller", blank=True, null=True)

    # Kanban
    column = models.ForeignKey("core.Column", on_delete=models.CASCADE, verbose_name="Coluna", related_name="cards_leads", blank=True, null=True)

    # Logs
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    history = HistoricalRecords()
    
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
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="Tarefa")
    file = models.FileField(verbose_name="Arquivo")
    description = models.TextField(verbose_name="Descrição")
    # Logs
    history = HistoricalRecords()

    def save(self, current_user=None, *args, **kwargs):
        if not self.id and current_user is not None:
            self.created_by = self.updated_by = current_user
        elif current_user is not None:
            self.updated_by = current_user
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.file.name
    
    class Meta:
        verbose_name = "Anexo"
        verbose_name_plural = "Anexos"


class Contact(models.Model):
    contact_type_choices = [
        ("email", "E-mail"),
        ("sms", "SMS")
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

    class Meta:
        verbose_name = "Campanha de Marketing"
        verbose_name_plural = "Campanhas de Marketing"


"""
class Opportunity(models.Model):
    Lead = models.ForeignKey(Lead, on_delete=models.CASCADE, verbose_name="Contato")
    stage = models.CharField(max_length=200, verbose_name="Estágio")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    expected_close_date = models.DateField(verbose_name="Data de Fechamento Esperada")

    board = ta:
        verbose_name = "Oportunidade"
        verbose_name_plural = "Oportunidades"


class ComercialProposal(models.Model):
    lead = models.CharField(max_length=255)
    kwp = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    # inverter_quantity = models.IntegerField()
    # inverter_simulation = models.CharField(max_length=255)
    # panel_quantity = models.IntegerField()
    # panel_name = models.CharField(max_length=255)
    # panel_power = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_generation = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_savings = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_area = models.DecimalField(max_digits=10, decimal_places=2)
    # kit_items = models.TextField()
    roi_years = models.DecimalField(max_digits=10, decimal_places=2)
    payback_graph = models.TextField()
    simulation_price = models.DecimalField(max_digits=10, decimal_places=2)
    financing_options = models.TextField()
    current_year_bill = models.DecimalField(max_digits=10, decimal_places=2)
    current_month_bill = models.DecimalField(max_digits=10, decimal_places=2)
    generator_year_bill = models.DecimalField(max_digits=10, decimal_places=2)
    generator_month_bill = models.DecimalField(max_digits=10, decimal_places=2)
    annual_savings = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_savings = models.DecimalField(max_digits=10, decimal_places=2)
    seller = models.CharField(max_length=255)
    branch = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.lead} - {self.kwp} kWp"
"""


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
    borrower = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Tomador", related_name="borrower_sales")
    seller = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Vendedor", related_name="seller_sales")
    sales_supervisor = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Supervisor de Vendas", related_name="supervisor_sales")
    sales_manager = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Gerente de Vendas", related_name="manager_sales")
    homologator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Homologador", related_name="homologator_sales")

    # Sale Information
    contract_number = models.CharField("Número do Contrato", max_length=20)
    contract_date = models.DateField("Data do Contrato")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Unidade")
    marketing_campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, verbose_name="Campanha de Marketing")

    # Document Information
    document_status = models.CharField("Status do Documento", max_length=2, choices=[("P", "Pendente"), ("F", "Finalizado"), ("EA", "Em Andamento"), ("C", "Cancelado"), ("D", "Distrato")])
    is_completed_document = models.BooleanField("Documento Completo", null=True, blank=True)
    document_situation = models.CharField("Situação do Documento", max_length=256, null=True, blank=True)
    document_completion_date = models.DateTimeField("Data de Conclusão do Documento", null=True, blank=True)

    # Financial Information
    financial_status = models.CharField("Status Financeiro", max_length=2, choices=[("P", "Pendente"), ("PA", "Parcial"), ("L", "Liquidado")])
    is_completed_financial = models.BooleanField("Financeiro Completo", null=True, blank=True)
    financial_completion_date = models.DateTimeField("Data de Conclusão Financeira", null=True, blank=True)
    project_value = models.DecimalField("Valor do Projeto", max_digits=20, decimal_places=6, default=0.000000)

    # Logs
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
    
    def __str__(self):
        return f'{self.contract_number} - {self.customer.name}'


class SaleDocument(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, verbose_name="Venda")
    document = models.FileField("Documento", upload_to="resolve_crm/sale_documents/")
    document_type = models.ForeignKey("contracts.DocumentType", on_delete=models.CASCADE, verbose_name="Tipo de Documento")
    status = models.CharField("Status", max_length=2, choices=[("P", "Pendente"), ("A", "Aprovado"), ("R", "Reprovado")])
    description = models.TextField("Descrição")
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    
    class Meta:
        verbose_name = "Documento da Venda"
        verbose_name_plural = "Documentos das Vendas"
    
    def __str__(self):
        return self.document.name
