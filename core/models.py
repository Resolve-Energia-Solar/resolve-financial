from django.utils.timezone import now
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy
from simple_history.models import HistoricalRecords
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import Max



class DocumentType(models.Model):
    
    APP_LABEL_CHOICES = (
        ('accounts', 'Contas'),
        ('contracts', 'Contratos'),
        ('field_services', 'Inspeções'),
        ('logistics', 'Logística'),
        ('resolve_crm', 'CRM'),
        ('core', 'Core'),
        ('engineering', 'Engenharia'),
        ('financial', 'Financeiro'),
    )
    
    name = models.CharField("Nome", max_length=100)
    app_label = models.CharField("App Label", max_length=100, choices=APP_LABEL_CHOICES)
    reusable = models.BooleanField("Reutilizável", default=False)
    required = models.BooleanField("Obrigatório", default=False)
    
    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DocumentSubType(models.Model):
    name = models.CharField("Nome", max_length=100)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, verbose_name="Tipo de Documento", related_name="subtypes")
    
    class Meta:
        verbose_name = "Subtipo de Documento"
        verbose_name_plural = "Subtipos de Documentos"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Attachment(models.Model):
    object_id = models.PositiveSmallIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    file = models.FileField("Arquivo", upload_to="resolve_crm/attachments/")
    status = models.CharField("Status", max_length=50, null=True, blank=True)
    document_type = models.ForeignKey("core.DocumentType", on_delete=models.CASCADE, verbose_name="Tipo de Documento", null=True, blank=True)
    document_subtype = models.ForeignKey("core.DocumentSubType", on_delete=models.CASCADE, verbose_name="Subtipo de Documento", null=True, blank=True)
    description = models.TextField("Descrição")
    # Logs
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    def file_name(self):
        return self.file.name.split('/')[-1]

    def file_or_image(self):
        if self.file.name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp')):
            return 'file-image'
        else:
            return 'file'

    def size(self):
        attachment_size = self.file.size
        if attachment_size < 1024 * 1024:
            return f"{attachment_size / 1024:.0f}KB"
        else:
            return f"{attachment_size / (1024 * 1024):.2f}MB"
        
    def __str__(self):
        return self.file.name
    
    class Meta:
        verbose_name = "Anexo"
        verbose_name_plural = "Anexos"
        ordering = ['-created_at']


class Comment(models.Model):
    object_id = models.PositiveSmallIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='comments')
    text = models.TextField("Comentário")
    # Logs
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.text
    
    class Meta:
        verbose_name = "Comentário"
        verbose_name_plural = "Comentários"
        ordering = ['-created_at']


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
    
    COLUMN_TYPES = (
        ('B', 'Backlog'),
        ('T', 'To Do'),
        ('I', 'In Progress'),
        ('D', 'Done'),
    )
    
    name = models.CharField("Nome", max_length=200)
    position = models.PositiveSmallIntegerField("Posição", blank=True, null=True)
    column_type = models.CharField("Tipo", max_length=1, choices=COLUMN_TYPES, blank=True, null=True, default='')
    board = models.ForeignKey('core.Board', related_name='columns', on_delete=models.PROTECT, verbose_name="Quadro")
    deadline = models.PositiveIntegerField("Prazo", blank=True, null=True)
    finished = models.BooleanField("Finalizado", default=False)
    color = models.CharField("Cor", max_length=7, blank=True, null=True)
    
    # Logs
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    @property
    def proposals_value(self):
        return sum([proposal.value for lead in self.leads.all() for proposal in lead.proposals.all()])
    
    def __str__(self):
        return f'{self.name} | {self.board}'
    
    def save(self, *args, **kwargs):
        if self.column_type is None:
            self.column_type = ''

        if self.column_type == 'D':
            self.finished = True

        if not self.position:
            max_position = Column.objects.filter(board=self.board).aggregate(Max('position'))['position__max']
            
            self.position = (max_position or 0) + 1

        super(Column, self).save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        if not self.column_type:
            self.column_type = ''
        
        super(Column, self).delete(*args, **kwargs)


    class Meta:
        verbose_name = 'Coluna'
        verbose_name_plural = 'Colunas'
        ordering = ['board', 'name','position']


class Task(models.Model):

    task_template = models.ForeignKey('core.TaskTemplates', related_name='tasks', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Modelo de Tarefa')
    
    project = models.ForeignKey('resolve_crm.Project', related_name='tasks', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Projeto')
    title = models.CharField(max_length=200)
    column = models.ForeignKey('core.Column', related_name='task', on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey('accounts.User', related_name='tasks_owned', on_delete=models.CASCADE, verbose_name='Responsável', blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    
    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    is_completed_date = models.DateTimeField(editable=False, blank=True, null=True)
    depends_on = models.ManyToManyField('core.Task', related_name='dependents', symmetrical=False, blank=True)
    is_archived = models.BooleanField(default=False, verbose_name='Arquivado')
    archived_at = models.DateTimeField(blank=True, null=True)
    id_integration = models.CharField(max_length=200, verbose_name='ID de Integração', blank=True, null=True)
    
    # Logs
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    
    def move_to_to_do(self):
        if not self.depends_on.filter(is_completed_date__isnull=True).exists():
            self.column = Column.objects.get(board=self.column.board, column_type='T')
            self.save()
    
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
    
    def save(self, *args, **kwargs):
        # Salva a instância pela primeira vez
        super(Task, self).save(*args, **kwargs)

        # Verifica se a tarefa está configurada para depender dela mesma
        if self.depends_on.filter(pk=self.pk).exists():
            raise ValueError('Task cannot depend on itself')

        # Verifica se a tarefa foi movida para a coluna "finished"
        if self.column.finished and not self.is_completed_date:
            self.is_completed_date = now()

            # Atualiza apenas o campo `is_completed_date`
            super(Task, self).save(update_fields=['is_completed_date'])

            # Move dependentes para "To Do"
            for dependent in self.dependents.all():
                dependent.move_to_to_do()


class TaskTemplates(models.Model):
    
    board = models.ForeignKey('core.Board', related_name='board_task_templates', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    component = models.CharField(max_length=200, blank=True, null=True)
    depends_on = models.ManyToManyField('core.TaskTemplates', related_name='dependents', symmetrical=False, blank=True)
    deadline = models.PositiveIntegerField()
    auto_create = models.BooleanField(default=False)
    column = models.ForeignKey('core.Column', related_name='column_tasks', on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.depends_on.filter(pk=self.pk).exists():
            raise ValueError('Task cannot depend on itself')
    
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
    event = models.CharField(max_length=1, choices=EVENT_CHOICES)
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


class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']


class TaggedItem(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="tagged_items")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = 'Item Taggeado'
        verbose_name_plural = 'Itens Taggeados'
