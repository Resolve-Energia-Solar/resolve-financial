from datetime import timedelta
from django.core.exceptions import FieldDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils.text import capfirst
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import ForeignKey, OneToOneField
from django.apps import apps

from api.views import BaseModelViewSet
from notifications.models import Notification
from resolve_crm.models import Sale

from .models import *
from .pagination import AttachmentPagination
from .serializers import *


class DocumentTypeViewSet(BaseModelViewSet):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    

class DocumentSubTypeViewSet(BaseModelViewSet):
    queryset = DocumentSubType.objects.all()
    serializer_class = DocumentSubTypeSerializer


class AttachmentViewSet(BaseModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    pagination_class = AttachmentPagination


class CommentViewSet(BaseModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


class ContentTypeViewSet(BaseModelViewSet):
    queryset = ContentType.objects.all().order_by('app_label', 'model')
    serializer_class = ContentTypeSerializer
    http_method_names = ['get']
    ordering_fields = ['app_label', 'model']


class BoardViewSet(BaseModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    
    
class ColumnViewSet(BaseModelViewSet):
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer
    

class TaskTemplatesViewSet(BaseModelViewSet):
    queryset = TaskTemplates.objects.all()
    serializer_class = TaskTemplatesSerializer


class TaskViewSet(BaseModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class HistoryView(APIView):
    http_method_names = ['get']

    def get(self, request):
        content_type_id = request.query_params.get('content_type')
        object_id = request.query_params.get('object_id')
        get_related = request.query_params.get('get_related', 'false').lower() == 'true'

        if not content_type_id or not object_id:
            return Response({
                'message': 'content_type e object_id são obrigatórios.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Busca o ContentType ou retorna 404 se não encontrado
        content_type = get_object_or_404(ContentType, id=content_type_id)
        model_class = content_type.model_class()

        # Busca o objeto principal
        try:
            obj = model_class.objects.get(id=object_id)
        except model_class.DoesNotExist:
            return Response({
                'message': 'Objeto não encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Função para buscar histórico de um objeto
        def get_object_history(object_instance, related_model_name=None, related_object_id=None):
            if not hasattr(object_instance, 'history'):
                return []

            history = object_instance.history.all()
            changes = []
            history_objects = list(history)

            for i in range(len(history_objects) - 1):
                new_record = history_objects[i]
                old_record = history_objects[i + 1]
                delta = new_record.diff_against(old_record)

                if delta.changes:
                    author_data = RelatedUserSerializer(new_record.history_user).data if new_record.history_user else {'username': 'Desconhecido'}
                    change_list = []
                    for change in delta.changes:
                        field_name = change.field
                        try:
                            field_verbose = new_record._meta.get_field(field_name).verbose_name
                        except FieldDoesNotExist:
                            field_verbose = field_name
                        field_verbose = capfirst(field_verbose)
                        change_list.append({
                            'field': field_name,
                            'field_label': field_verbose,
                            'old': change.old,
                            'new': change.new
                        })
                    changes.append({
                        'timestamp': new_record.history_date,
                        'history_type': new_record.history_type,
                        'author': author_data,
                        'model': related_model_name or object_instance.__class__.__name__,
                        'object_id': related_object_id or object_instance.id,
                        'changes': change_list
                    })

            return changes

        # Consolidar histórico
        unified_history = []

        # Adiciona histórico do objeto principal
        unified_history.extend(get_object_history(obj))

        # Busca objetos relacionados dinamicamente apenas se `get_related` for `true`
        if get_related:
            for model in apps.get_models():
                for field in model._meta.fields:
                    if isinstance(field, (ForeignKey, OneToOneField)) and field.related_model == model_class:
                        related_objects = model.objects.filter(**{field.name: obj})
                        for related_obj in related_objects:
                            unified_history.extend(
                                get_object_history(related_obj, related_model_name=model.__name__, related_object_id=related_obj.id)
                            )

        # Ordena o histórico pela timestamp
        unified_history = sorted(unified_history, key=lambda x: x['timestamp'], reverse=True)

        return Response({
            'history': unified_history
        }, status=status.HTTP_200_OK)


class NotificationViewSet(BaseModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer


class CreateTasksFromSaleView(APIView):
    def post(self, request, *args, **kwargs):
        sale_id = request.data.get('sale_id')
        if not sale_id:
            return Response({"error": "sale_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifica se a venda existe
        try:
            sale = Sale.objects.get(pk=sale_id)
        except Sale.DoesNotExist:
            return Response({"error": "Sale not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Obtém o ContentType da venda
        sale_content_type = ContentType.objects.get_for_model(Sale)
        
        # Filtra os templates relacionados à venda com auto_create=True
        task_templates = TaskTemplates.objects.filter(content_type=sale_content_type, auto_create=True)
        
        # Dicionário para mapear templates e tarefas criadas
        template_task_map = {}

        # Criação de tarefas para os templates de venda
        for template in task_templates:
            task = Task.objects.create(
                task_template=template,
                title=template.title,
                column=template.column,
                description=template.description,
                due_date=sale.created_at + timedelta(days=template.deadline),
                owner=None,
                object_id=sale.pk
            )
            template_task_map[template] = task

        # Configuração de dependências entre tarefas
        for template, task in template_task_map.items():
            dependencies = template.depends_on.all()  # Templates dos quais este depende
            for dependency_template in dependencies:
                if dependency_template in template_task_map:
                    dependent_task = template_task_map[dependency_template]
                    task.depends_on.add(dependent_task)

        # Lógica adicional para projetos relacionados
        if sale.projects.exists():
            project_content_type = ContentType.objects.get_for_model(sale.projects.model)
            project_templates = TaskTemplates.objects.filter(content_type=project_content_type, auto_create=True)

            for project in sale.projects.all():
                for template in project_templates:
                    task = Task.objects.create(
                        task_template=template,
                        project=project,
                        title=template.title,
                        column=template.column,
                        description=template.description,
                        due_date=project.created_at + timedelta(days=template.deadline),
                        owner=None,
                        object_id=project.pk
                    )
                    template_task_map[template] = task

            # Configuração de dependências entre tarefas de projetos
            for template, task in template_task_map.items():
                dependencies = template.depends_on.all()  # Templates dos quais este depende
                for dependency_template in dependencies:
                    if dependency_template in template_task_map:
                        dependent_task = template_task_map[dependency_template]
                        task.depends_on.add(dependent_task)

        return Response(
            {"message": "Tasks created successfully", "tasks": [t.title for t in template_task_map.values()]},
            status=status.HTTP_201_CREATED
        )
