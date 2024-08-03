from django.db import models
from django.urls import reverse_lazy
from simple_history.models import HistoricalRecords


class Lead(models.Model):

    # Personal Information
    name = models.CharField(max_length=200, verbose_name="Nome")
    type = models.CharField(max_length=200, verbose_name="Tipo", help_text="Pessoa Física ou Jurídica?", choices=[("PF", "Pessoa Física"), ("PJ", "Pessoa Jurídica")])

    # Lead
    contact_email = models.EmailField(verbose_name="E-mail")
    phone = models.CharField(max_length=20, verbose_name="Telefone")
    address = models.ForeignKey("accounts.Address", on_delete=models.CASCADE, verbose_name="Endereço", blank=True, null=True)
    
    # CRM Information

    origin = models.CharField(max_length=200, verbose_name="Origem", blank=True, null=True)
    squad = models.ForeignKey("resolve_crm.Squad", on_delete=models.CASCADE, verbose_name="Squad")
    responsible = models.ForeignKey("accounts.User", on_delete=models.CASCADE, verbose_name="Responsável", related_name="lead_responsible", blank=True, null=True)
    seller = models.ForeignKey("accounts.User", on_delete=models.CASCADE, verbose_name="Vendedor", related_name="lead_seller", blank=True, null=True)
    # Kanban
    column = models.ForeignKey("core.Column", on_delete=models.CASCADE, verbose_name="Coluna", related_name="cards_leads", blank=True, null=True)
    # Logs
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


"""
class Opportunity(models.Model):
    Lead = models.ForeignKey(Lead, on_delete=models.CASCADE, verbose_name="Contato")
    stage = models.CharField(max_length=200, verbose_name="Estágio")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    expected_close_date = models.DateField(verbose_name="Data de Fechamento Esperada")

    board = ta:
        verbose_name = "Oportunidade"
        verbose_name_plural = "Oportunidades"


class MarketingCampaign(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nome")
    start_date = models.DateField(verbose_name="Data de Início")
    end_date = models.DateField(verbose_name="Data de Término")
    effectiveness = models.TextField(verbose_name="Eficácia")

    class Meta:
        verbose_name = "Campanha de Marketing"
        verbose_name_plural = "Campanhas de Marketing"


class CustomerLifeCycle(models.Model):
    Lead = models.ForeignKey(Lead, on_delete=models.CASCADE, verbose_name="Contato")
    stage = models.CharField(max_length=200, verbose_name="Estágio")
    start_date = models.DateField(verbose_name="Data de Início")
    end_date = models.DateField(verbose_name="Data de Término")

    class Meta:
        verbose_name = "Ciclo de Vida do Cliente"
        verbose_name_plural = "Ciclos de Vida dos Clientes"
"""