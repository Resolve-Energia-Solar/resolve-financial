from django.db import models
from simple_history.models import HistoricalRecords


class RoofType(models.Model):
    name = models.CharField(max_length=50, verbose_name="Nome", blank=True, null=True)
    is_deleted = models.BooleanField(verbose_name="Deletado", default=False)
    created_at = models.DateTimeField(verbose_name="Criado em", auto_now_add=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de Telhado"
        verbose_name_plural = "Tipos de Telhados"
        ordering = ["name"]


class Category(models.Model):
    name = models.CharField("Nome da Categoria", max_length=50, unique=True)
    members = models.ManyToManyField("accounts.User", verbose_name="Membros", blank=True)
    main_category = models.ForeignKey("self", verbose_name="Categoria Principal", on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name 
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["name"]

class Deadline(models.Model):
    name = models.CharField("Nome do Prazo", max_length=50, unique=True)
    hours = models.TimeField("Horas", blank=True, null=True)
    observation = models.TextField("Observação", blank=True, null=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Prazo"
        verbose_name_plural = "Prazos"
        ordering = ["name"]

    
class Service(models.Model):
    name = models.CharField("Nome do Serviço", max_length=50, unique=True)
    category = models.ForeignKey(Category, verbose_name="Categoria", on_delete=models.CASCADE)
    description = models.TextField("Descrição", blank=True, null=True)
    deadline = models.ForeignKey(Deadline, verbose_name="Prazo", on_delete=models.CASCADE, blank=True, null=True)
    form = models.ForeignKey("Forms", verbose_name="Formulário", on_delete=models.CASCADE, blank=False, null=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ["name"]


class Forms(models.Model):
    name = models.CharField("Nome do Formulário", max_length=50, unique=True)
    campos = models.JSONField("Campos", blank=True, null=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    history = HistoricalRecords()

    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Formulário"
        verbose_name_plural = "Formulários"
        ordering = ["name"]


class Answer(models.Model):
    form = models.ForeignKey(Forms, verbose_name="Formulário", on_delete=models.CASCADE)
    answers = models.JSONField("Respostas", blank=True, null=True)
    answerer = models.ForeignKey("accounts.User", verbose_name="Respondente", on_delete=models.CASCADE)
    schedule = models.ForeignKey("Schedule", verbose_name="Agendamento", on_delete=models.CASCADE)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Resposta"
        verbose_name_plural = "Respostas"
        ordering = ["-created_at"]


class Schedule(models.Model):
    status_choices = [
        ("Pendente", "Pendente"),
        ("Concluído", "Concluído"),
        ("Cancelado", "Cancelado"),
    ]

    schedule_creator = models.ForeignKey("accounts.User", verbose_name="Criador do Agendamento", on_delete=models.CASCADE, related_name='schedule_creator')
    schedule_date = models.DateField("Data do Agendamento")
    schedule_start_time = models.TimeField("Horário de Início")
    schedule_end_time = models.TimeField("Horário de Fim")
    products = models.ManyToManyField("logistics.Product", verbose_name="Produtos", blank=True)
    service = models.ForeignKey(Service, verbose_name="Serviço", on_delete=models.CASCADE)
    project = models.ForeignKey("resolve_crm.Project", verbose_name="Projeto", on_delete=models.CASCADE, related_name='field_services')
    address = models.ForeignKey("accounts.Address", verbose_name="Endereço", on_delete=models.CASCADE)
    latitude = models.CharField("Latitude", max_length=50, blank=True, null=True)
    longitude = models.CharField("Longitude", max_length=50, blank=True, null=True)
    schedule_agent = models.ForeignKey("accounts.User", verbose_name="Agente de Campo", on_delete=models.CASCADE, related_name='schedule_agent')
    going_to_location_at = models.DateTimeField("Indo para o Local em", blank=True, null=True)
    execution_started_at = models.DateTimeField("Execução Iniciada em", blank=True, null=True)
    execution_finished_at = models.DateTimeField("Execução Finalizada em", blank=True, null=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    status = models.CharField("Status", max_length=50, choices=status_choices, default="Pendente")
    is_deleted = models.BooleanField("Deletado", default=False)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ["-created_at"]

class BlockTimeAgent(models.Model):
    agent = models.ForeignKey("accounts.User", verbose_name="Agente", on_delete=models.CASCADE)
    start_date = models.DateField("Data de Início")
    end_date = models.DateField("Data de Fim")
    start_time = models.TimeField("Horário de Início")
    end_time = models.TimeField("Horário de Fim")
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Bloqueio de Horário"
        verbose_name_plural = "Bloqueios de Horário"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=['agent', 'start_date', 'end_date', 'start_time', 'end_time'], name='unique_block_time_agent')
        ]

class FreeTimeAgent(models.Model):
    day_of_week = [
        (0, "Segunda-feira"),
        (1, "Terça-feira"),
        (2, "Quarta-feira"),
        (3, "Quinta-feira"),
        (4, "Sexta-feira"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    agent = models.ForeignKey("accounts.User", verbose_name="Agente", on_delete=models.CASCADE)
    day_of_week = models.IntegerField("Dia da Semana", choices=day_of_week)
    start_time = models.TimeField("Horário de Início")
    end_time = models.TimeField("Horário de Fim")
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Disponibilidade de Horário"
        verbose_name_plural = "Disponibilidades de Horário"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=['agent', 'day_of_week'], name='unique_free_time_agent')
        ]
