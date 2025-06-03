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
    
    # Monitoring
    answered_at = models.DateTimeField(
        "Respondido em",
        blank=True,
        null=True,
        help_text="Data e hora em que o chamado foi respondido",
    )
    answered_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        verbose_name="Respondido por",
        related_name="answered_tickets",
        blank=True,
        null=True,
    )
    closed_at = models.DateTimeField(
        "Fechado em",
        blank=True,
        null=True,
        help_text="Data e hora em que o chamado foi fechado",
    )
    closed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        verbose_name="Fechado por",
        related_name="closed_tickets",
        blank=True,
        null=True,
    )
    resolved_at = models.DateTimeField(
        "Resolvido em",
        blank=True,
        null=True,
        help_text="Data e hora em que o chamado foi resolvido",
    )
    resolved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        verbose_name="Resolvido por",
        related_name="resolved_tickets",
        blank=True,
        null=True,
    )
    
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)
    is_deleted = models.BooleanField("Deletado", default=False)

    history = HistoricalRecords()
    
    def save(self, *args, **kwargs):
        """
        Override do save para:
        - popular answered_at / answered_by quando status passar a 'RE'
        - popular resolved_at / resolved_by quando status passar a 'R'
        - popular closed_at / closed_by quando status passar a 'F'
        - manter a lógica de conclusion_date (quando status for 'R' ou 'F')
        """
        # 1) Obter o usuário atual, se passado como argumento
        current_user = kwargs.pop("current_user", None)

        # 2) Verificar se já existe essa instância no banco (para comparar o status antigo)
        if self.pk:
            # Busco apenas o campo 'status' antigo; evita carregar tudo
            old = Ticket.objects.filter(pk=self.pk).values("status").first()
            old_status = old["status"] if old else None
        else:
            old_status = None

        # 3) Se status mudou para 'RE' (Respondido) E ainda não tem answered_at
        if self.status == "RE" and old_status != "RE" and not self.answered_at:
            self.answered_at = timezone.now()
            if current_user:
                self.answered_by = current_user

        # 4) Se status mudou para 'R' (Resolvido) E ainda não tem resolved_at
        if self.status == "R" and old_status != "R" and not self.resolved_at:
            self.resolved_at = timezone.now()
            if current_user:
                self.resolved_by = current_user

        # 5) Se status mudou para 'F' (Fechado) E ainda não tem closed_at
        if self.status == "F" and old_status != "F" and not self.closed_at:
            self.closed_at = timezone.now()
            if current_user:
                self.closed_by = current_user

        # 6) Lógica anterior: se status for 'R' ou 'F' e conclusion_date vazio, preenche
        if not self.conclusion_date and self.status in ("R", "F"):
            self.conclusion_date = timezone.now()

        # 7) Chamamos o save real
        super().save(*args, **kwargs)

        # 8) Atualizar o atributo interno para não revalidar na próxima chamada
        self._original_status = self.status

        
    
    @property
    def open_duration(self):
        início = self.created_at
        if self.status in ("R", "F") and self.conclusion_date:
            return self.conclusion_date - início
        return timezone.now() - início

    class Meta:
        verbose_name = "Chamado"
        verbose_name_plural = "Chamados"
        ordering = ["-created_at"]
        
    def __str__(self):
        return f"{self.subject} - {self.project.project_number} ({self.get_status_display()})"


    