from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy
from simple_history.models import HistoricalRecords


class BoardTemplate(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nome")
    description = models.TextField(verbose_name="Descrição", blank=True, null=True)
    # Logs
    history = HistoricalRecords()

    def save(self, current_user=None, *args, **kwargs):
        if not self.id and current_user is not None:
            self.created_by = self.updated_by = current_user
        elif current_user is not None:
            self.updated_by = current_user
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse_lazy('resolve_crm:board-template-detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Modelo de Quadro"
        verbose_name_plural = "Modelos de Quadros"
        ordering = ["name"]


class Board(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    branch = models.ForeignKey('accounts.Branch', related_name='boards', on_delete=models.CASCADE)
    # Logs
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.title


class Column(models.Model):
    title = models.CharField(max_length=200)
    board = models.ForeignKey('Board', related_name='columns', on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()
    # Logs
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.title


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    owner = models.ForeignKey('accounts.User', related_name='tasks_owned', on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    is_completed_date = models.DateTimeField(editable=False)
    column = models.ForeignKey('core.Column', related_name='tasks', on_delete=models.CASCADE)
    depends_on = models.ManyToManyField('core.Task', related_name='dependents', symmetrical=False)
    object_id = models.PositiveSmallIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True)
    id_integration = models.CharField(max_length=200)
    # Logs
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    
    def get_object(self):
        return self.content_type.get_object_for_this_type(pk=self.object_id)

    def __str__(self):
        return self.title
