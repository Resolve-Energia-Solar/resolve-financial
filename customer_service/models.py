from django.db import models
from simple_history.models import HistoricalRecords
from django.utils import timezone


class CustomerService(models.Model):

    customer = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, verbose_name="Cliente", blank=True, null=True
    )
    protocol = models.BigIntegerField("Protocolo")
    user = models.CharField("Usuário", max_length=50)
    service = models.PositiveIntegerField("Atendimento")
    date = models.DateField("Data")

    class Meta:
        verbose_name = "Atendimento"
        verbose_name_plural = "Atendimentos"

    def __str__(self):
        return f"{self.protocol} - {self.customer.complete_name}"



class LostReason(models.Model):
    name = models.CharField("Motivo", max_length=50)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Motivo de Perda"
        verbose_name_plural = "Motivos de Perda"

    def __str__(self):
        return self.name


class TicketType(models.Model):
    name = models.CharField("Tipo de Chamado", max_length=50)
    deadline = models.DurationField(
        "Prazo (Horas)",
        help_text="Prazo em horas para resolução do chamado",
    )
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Tipo de Chamado"
        verbose_name_plural = "Tipos de Chamados"

    def __str__(self):
        return self.name



class Ticket(models.Model):
    project = models.ForeignKey(
        "resolve_crm.Project", on_delete=models.CASCADE, verbose_name="Projeto", related_name="project_tickets"
    )
    responsible = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        verbose_name="Responsável",
        related_name="responsible_tickets",
    )
    subject = models.CharField("Assunto", max_length=100)
    description = models.TextField("Descrição", blank=True, null=True)
    ticket_type = models.ForeignKey(
        "TicketType",
        on_delete=models.CASCADE,
        verbose_name="Tipo de Chamado",
        related_name="ticket_type_tickets",
    )
    priority = models.PositiveSmallIntegerField(
        "Prioridade",
        choices=[
            (1, "Baixa"),
            (2, "Média"),
            (3, "Alta"),
        ],
    )
    responsible_department = models.ForeignKey(
        "accounts.Department",
        on_delete=models.CASCADE,
        verbose_name="Departamento Responsável",
        related_name="responsible_department_tickets",
    )
    responsible_user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        verbose_name="Usuário Responsável",
        related_name="responsible_user_tickets",
    )
    status = models.CharField(
        "Status",
        max_length=20,
        choices=[
            ("A", "Aberto"),
            ("E", "Em Espera"),
            ("RE", "Respondido"),
            ("R", "Resolvido"),
            ("F", "Fechado"),
        ],
        default="A",
    )
    conclusion_date = models.DateTimeField(
        "Data de Conclusão",
        blank=True,
        null=True,
        help_text="Data em que o chamado foi concluído",
    )
    deadline = models.DurationField(
        "Prazo (Em horas)",
        help_text="Prazo em horas para resolução do chamado",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)
    is_deleted = models.BooleanField("Deletado", default=False)

    history = HistoricalRecords()
    
    def save(self, *args, **kwargs):
        if not self.conclusion_date and (self.status == "R" or self.status == "F"):
            self.conclusion_date = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Chamado"
        verbose_name_plural = "Chamados"
        ordering = ["-created_at"]
        
    def __str__(self):
        return f"{self.subject} - {self.project.project_number} ({self.get_status_display()})"


    