import graphene
from graphene_django.types import DjangoObjectType
from .models import Board, Column, Task, TaskTemplates, Webhook

class BoardType(DjangoObjectType):
    class Meta:
        model = Board
        fields = "__all__"

class ColumnType(DjangoObjectType):
    class Meta:
        model = Column
        fields = "__all__"

class TaskType(DjangoObjectType):
    class Meta:
        model = Task
        fields = "__all__"

class TaskTemplatesType(DjangoObjectType):
    class Meta:
        model = TaskTemplates
        fields = "__all__"

class WebhookType(DjangoObjectType):
    class Meta:
        model = Webhook
        fields = "__all__"

class Query(graphene.ObjectType):
    boards = graphene.List(BoardType)
    columns = graphene.List(ColumnType)
    tasks = graphene.List(TaskType)
    task_templates = graphene.List(TaskTemplatesType)
    webhooks = graphene.List(WebhookType)

    def resolve_boards(self, info, **kwargs):
        return Board.objects.all()

    def resolve_columns(self, info, **kwargs):
        return Column.objects.all()

    def resolve_tasks(self, info, **kwargs):
        return Task.objects.all()

    def resolve_task_templates(self, info, **kwargs):
        return TaskTemplates.objects.all()

    def resolve_webhooks(self, info, **kwargs):
        return Webhook.objects.all()

# Crie o schema com a query definida
schema = graphene.Schema(query=Query)
