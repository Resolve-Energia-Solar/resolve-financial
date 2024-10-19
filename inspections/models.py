from django.db import models
from simple_history.models import HistoricalRecords

class RoofType(models.Model):
    name = models.CharField(max_length=50, verbose_name="Nome", blank=True, null=True)
    is_deleted = models.BooleanField(verbose_name="Deletado", default=False)
    created_at = models.DateTimeField(verbose_name="Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Tipo de Telhado"
        verbose_name_plural = "Tipos de Telhados"

class Category(models.Model):
    name = models.CharField("Nome da Categoria", max_length=50, unique=True)
    squads = models.ManyToManyField("accounts.Squad", verbose_name="Squads", related_name='categories', blank=True)
    main_category = models.ForeignKey("self", verbose_name="Categoria Principal", on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name 
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

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
    
class Service(models.Model):
    name = models.CharField("Nome do Serviço", max_length=50, unique=True)
    category = models.ForeignKey(Category, verbose_name="Categoria", on_delete=models.CASCADE)
    description = models.TextField("Descrição", blank=True, null=True)
    deadline = models.ForeignKey(Deadline, verbose_name="Prazo", on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    history = HistoricalRecords()
    
    def __str__(self):
        return '{} - {}'.format(self.name, self.deadline)
    
    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"

class Forms(models.Model):
    name = models.CharField("Nome do Formulário", max_length=50, unique=True)
    service = models.ForeignKey(Service, verbose_name="Serviço", on_delete=models.CASCADE)
    campos = models.JSONField("Campos", blank=True, null=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    history = HistoricalRecords()

    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Formulário"
        verbose_name_plural = "Formulários"

class Answer(models.Model):
    form = models.ForeignKey(Forms, verbose_name="Formulário", on_delete=models.CASCADE)
    answers = models.JSONField("Respostas", blank=True, null=True)
    answerer = models.ForeignKey("accounts.User", verbose_name="Respondente", on_delete=models.CASCADE)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Resposta"
        verbose_name_plural = "Respostas"

class Schedule(models.Model):
    status_choices = [
        ("Pendente", "Pendente"),
        ("Concluído", "Concluído"),
        ("Cancelado", "Cancelado"),
    ]

    schedule_creator = models.ForeignKey("accounts.User", verbose_name="Criador do Agendamento", on_delete=models.CASCADE, related_name='schedule_creator')
    schedule_date = models.DateTimeField("Data do Agendamento")
    service = models.ForeignKey(Service, verbose_name="Serviço", on_delete=models.CASCADE)
    project = models.ForeignKey("resolve_crm.Project", verbose_name="Projeto", on_delete=models.CASCADE)
    location = models.CharField("Local", max_length=50, blank=True, null=True)
    schedule_agent = models.ForeignKey("accounts.User", verbose_name="Agente de Campo", on_delete=models.CASCADE, related_name='schedule_agent')
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    status = models.CharField("Status", max_length=50, choices=status_choices, default="Pendente")
    is_deleted = models.BooleanField("Deletado", default=False)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"