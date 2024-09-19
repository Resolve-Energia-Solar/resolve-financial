from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy
from simple_history.models import HistoricalRecords


class Column(models.Model):
    
    name = models.CharField("Nome", max_length=200)
    position = models.PositiveSmallIntegerField("Posição")
    board = models.ForeignKey('core.Board', related_name='columns', on_delete=models.CASCADE, verbose_name="Quadro")
    
    # Logs
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

class Board(models.Model):
    
    title = models.CharField("Título", max_length=200)
    description = models.TextField("Descrição")
    branch = models.ForeignKey('accounts.Branch', related_name='boards', on_delete=models.CASCADE, verbose_name="Unidade")
    
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


class Task(models.Model):
    
    task_template = models.ForeignKey('core.TaskTemplates', related_name='tasks', on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    owner = models.ForeignKey('accounts.User', related_name='tasks_owned', on_delete=models.CASCADE)
    board = models.ForeignKey('core.Board', related_name='board_tasks', on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    is_completed_date = models.DateTimeField(editable=False, blank=True, null=True)
    depends_on = models.ManyToManyField('core.Task', related_name='dependents', symmetrical=False)
    object_id = models.PositiveSmallIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(blank=True, null=True)
    id_integration = models.CharField(max_length=200)
    
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


class TaskTemplates(models.Model):
    
    title = models.CharField(max_length=200)
    depends_on = models.ManyToManyField('core.TaskTemplates', related_name='dependents', symmetrical=False)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'Modelo de Tarefa'
        verbose_name_plural = 'Modelos de Tarefas'
    

class Webhook(models.Model):
    
    url = models.URLField()
    secret = models.CharField(max_length=200)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    event = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    
    # Logs
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.url
    
    class Meta:
        verbose_name = 'Webhook'
        verbose_name_plural = 'Webhooks'