from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy
from simple_history.models import HistoricalRecords



class Board(models.Model):
    
    title = models.CharField("Título", max_length=200)
    description = models.TextField("Descrição")
    branch = models.ForeignKey('accounts.Branch', related_name='boards', on_delete=models.CASCADE, verbose_name="Unidade")
    is_lead = models.BooleanField("lead?", default=False)
    
    # Logs
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    def get_absolute_url(self):
        return reverse_lazy('core:board-kanban', kwargs={'pk': self.pk})

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'Quadro'
        verbose_name_plural = 'Quadros'
        ordering = ['title']


class Column(models.Model):
    
    name = models.CharField("Nome", max_length=200)
    position = models.PositiveSmallIntegerField("Posição",blank=False, null=False)
    board = models.ForeignKey('core.Board', related_name='columns', on_delete=models.CASCADE, verbose_name="Quadro")
    finished = models.BooleanField("Finalizado", default=False)
    
    # Logs
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Coluna'
        verbose_name_plural = 'Colunas'
        ordering = ['position']


class Task(models.Model):
    
    project = models.ForeignKey('resolve_crm.Project', related_name='tasks', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Projeto')
    title = models.CharField(max_length=200)
    column = models.ForeignKey('core.Column', related_name='task', on_delete=models.CASCADE)
    description = models.TextField()
    owner = models.ForeignKey('accounts.User', related_name='tasks_owned', on_delete=models.CASCADE, verbose_name='Responsável')
    board = models.ForeignKey('core.Board', related_name='board_tasks', on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False, verbose_name='Concluído')
    start_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    is_completed_date = models.DateTimeField(editable=False, blank=True, null=True)
    depends_on = models.ManyToManyField('core.Task', related_name='dependents', symmetrical=False, blank=True)
    # object_id = models.PositiveSmallIntegerField()
    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    is_archived = models.BooleanField(default=False, verbose_name='Arquivado')
    archived_at = models.DateTimeField(blank=True, null=True)
    id_integration = models.CharField(max_length=200, verbose_name='ID de Integração', blank=True, null=True)
    
    # Logs
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    
    def get_absolute_url(self):
        url = f'{self.content_type.app_label}:{self.content_type.model}_detail'
        return reverse_lazy(url, kwargs={'pk': self.object_id})
    
    def get_object(self):
        return self.content_type.get_object_for_this_type(pk=self.object_id)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'
        ordering = ['-due_date']


class TaskTemplates(models.Model):
    
    board = models.ForeignKey('core.Board', related_name='board_task_templates', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    depends_on = models.ManyToManyField('core.TaskTemplates', related_name='dependents', symmetrical=False)
    column = models.ForeignKey('core.Column', related_name='column_tasks', on_delete=models.CASCADE)
    description = models.TextField()
    
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'Modelo de Tarefa'
        verbose_name_plural = 'Modelos de Tarefas'
        ordering = ['title']
    

class Webhook(models.Model):
    
    EVENT_CHOICES = (
        ('C', 'Create'),
        ('U', 'Update'),
        ('D', 'Delete'),
    )
    
    url = models.URLField()
    secret = models.CharField(max_length=200, blank=True, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    event = models.CharField(max_length=1, choices=EVENT_CHOICES)  # Usa choices e define o tamanho correto
    is_active = models.BooleanField(default=True)
    
    # Logs
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.url
    
    class Meta:
        verbose_name = 'Webhook'
        verbose_name_plural = 'Webhooks'
        ordering = ['-created_at']
