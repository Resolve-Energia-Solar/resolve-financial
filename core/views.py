from datetime import timedelta
from django.core.exceptions import FieldDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils.text import capfirst
from rest_framework import status
from rest_framework.permissions import AllowAny
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


class SystemConfigView(APIView):
    
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post']
    
    
    def get(self, request):
        config = SystemConfig.objects.first()
        if config:
            serializer = SystemConfigSerializer(config)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Nenhuma configuração."}, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request):
        if 'configs' not in request.data:
            return Response({'detail': 'Atributo "configs" não especificado'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        config, _ = SystemConfig.objects.get_or_create(id=1)
        serializer = SystemConfigSerializer(config, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    
    def get_queryset(self):
        return self.request.user.notifications.all()


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
        
        # Filtra os templates com auto_create=True
        task_templates = TaskTemplates.objects.filter(auto_create=True)
        
        # Dicionário para mapear templates e tarefas criadas (usando template e projeto como chave)
        template_task_map = {}

        # Criação de tarefas para os projetos associados à venda
        for project in sale.projects.all():
            for template in task_templates:
                # Define o object_id com base no tipo de template
                object_id = None
                if template.content_type.model == 'project':
                    object_id = project.pk
                elif template.content_type.model == 'sale':
                    object_id = sale.pk

                # Cria a tarefa com o project e/ou object_id apropriados
                task = Task.objects.create(
                    task_template=template,
                    title=template.title,
                    column=template.column,
                    description=template.description,
                    due_date=project.created_at + timedelta(days=template.deadline),
                    owner=None,
                    object_id=object_id,
                    project=project
                )
                # Adiciona ao mapeamento usando o template e o projeto
                template_task_map[(template, project)] = task

        # Configuração de dependências entre tarefas
        for (template, project), task in template_task_map.items():
            dependencies = template.depends_on.all()
            for dependency_template in dependencies:
                # Busca a tarefa dependente usando o mesmo projeto
                dependent_task = template_task_map.get((dependency_template, project))
                if dependent_task:
                    task.depends_on.add(dependent_task)

        return Response(
            {"message": "Tasks created successfully", "tasks": [t.title for t in template_task_map.values()]},
            status=status.HTTP_201_CREATED
        )
