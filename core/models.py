from django.db import models
from django.contrib.contenttypes.models import ContentType


class Board(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    # Logs
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Column(models.Model):
    title = models.CharField(max_length=200)
    board = models.ForeignKey('Board', related_name='columns', on_delete=models.CASCADE)
    # Logs
    created_at = models.DateTimeField(auto_now_add=True)

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
    
    def get_object(self):
        return self.content_type.get_object_for_this_type(pk=self.object_id)

    def __str__(self):
        return self.title
