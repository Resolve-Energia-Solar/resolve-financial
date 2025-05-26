from copy import deepcopy
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
from accounts.serializers import ContentTypeSerializer, UserSerializer
from api.views import BaseModelViewSet
from notifications.models import Notification
from resolve_crm.models import Sale
from django.utils import timezone
from .models import *
from .pagination import AttachmentPagination
from .serializers import *
from rest_framework import generics


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
            return Response(
                {'message': 'content_type e object_id são obrigatórios.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        content_type = get_object_or_404(ContentType, id=content_type_id)
        model_class = content_type.model_class()

        # Pré-fetch relações pertinentes
        related_names = [rel.get_accessor_name() for rel in model_class._meta.related_objects]
        try:
            obj = model_class.objects.prefetch_related(*related_names).get(id=object_id)
        except model_class.DoesNotExist:
            return Response(
                {'message': 'Objeto não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # IDs e mapeamento de modelos
        obj_ids = [obj.id]
        model_names = {obj.id: model_class.__name__}
        if get_related:
            for rel in model_class._meta.related_objects:
                for related in getattr(obj, rel.get_accessor_name()).all():
                    obj_ids.append(related.id)
                    model_names[related.id] = rel.related_model.__name__

        # Paginação
        try:
            limit = int(request.query_params.get('limit', 100))
            offset = int(request.query_params.get('offset', 0))
        except ValueError:
            return Response(
                {'message': 'Parâmetros limit e offset devem ser inteiros.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        start, end = offset, offset + limit + 1

        # Batch fetch do histórico
        HistoryModel = obj.history.model
        records = list(
            HistoryModel.objects
            .filter(id__in=obj_ids)
            .select_related('history_user')
            .order_by('-history_date')[start:end]
        )

        # Cache para verbose_name de campos
        verbose_cache = {}
        def get_verbose_name(field, meta):
            key = (meta, field)
            if key not in verbose_cache:
                try:
                    verbose_cache[key] = capfirst(meta.get_field(field).verbose_name)
                except Exception:
                    verbose_cache[key] = field
            return verbose_cache[key]

        # Agrupa por objeto e gera diffs
        grouped = {}
        for rec in records:
            grouped.setdefault(rec.id, []).append(rec)

        unified = []
        for oid, recs in grouped.items():
            for new, old in zip(recs, recs[1:]):
                delta = new.diff_against(old)
                if not delta.changes:
                    continue
                user = new.history_user
                if user:
                    author = {
                        'id': user.id,
                        'complete_name': getattr(user, 'complete_name', user.get_full_name()),
                        'email': user.email,
                        'username': user.username,
                    }
                else:
                    author = {
                        'id': None,
                        'complete_name': None,
                        'email': None,
                        'username': 'Desconhecido',
                    }
                changes = []
                for change in delta.changes:
                    label = get_verbose_name(change.field, new._meta)
                    changes.append({
                        'field': change.field,
                        'field_label': label,
                        'old': change.old,
                        'new': change.new,
                    })
                unified.append({
                    'timestamp': new.history_date,
                    'history_type': new.history_type,
                    'author': author,
                    'model': model_names.get(oid, model_class.__name__),
                    'object_id': oid,
                    'changes': changes,
                })

        # Ordenação e paginação final
        unified.sort(key=lambda x: x['timestamp'], reverse=True)
        paginated = unified[:limit]

        return Response({
            'count': len(unified),
            'offset': offset,
            'limit': limit,
            'history': paginated,
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


class TagViewSet(BaseModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    
    
class ProcessViewSet(BaseModelViewSet):
    queryset = Process.objects.all()
    serializer_class = ProcessSerializer


class ProcessDetailView(generics.RetrieveAPIView):
    queryset = Process.objects.all()
    serializer_class = ProcessSerializer
    

class ProcessByObjectView(generics.RetrieveAPIView):
    serializer_class = ProcessSerializer

    def get(self, request, *args, **kwargs):
        app_label = kwargs.get("app_label")
        model_name = kwargs.get("model")
        object_id = kwargs.get("object_id")

        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model_name)
        except ContentType.DoesNotExist:
            return Response({"error": "ContentType não encontrado"}, status=400)

        process = get_object_or_404(Process, content_type=content_type, object_id=object_id)
        serializer = self.get_serializer(process)
        return Response(serializer.data)
    


class FinishStepView(APIView):
    def patch(self, request, process_id, id):
        process = get_object_or_404(Process, id=process_id)
        user_id = request.data.get('user_id') or request.user.id

        if user_id != request.user.id:
            return Response({'error': 'Você não tem permissão para concluir esta etapa.'}, status=403)

        steps = process.steps or []

        if not steps:
            return Response({'error': 'Nenhuma etapa encontrada.'}, status=404)

        try:
            etapa_id = int(id)
        except ValueError:
            return Response({'error': 'ID da etapa inválido.'}, status=400)

        etapa_encontrada = next((et for et in steps if et.get("id") == etapa_id), None)

        if not etapa_encontrada:
            return Response({'error': 'Etapa não encontrada.'}, status=404)

        if etapa_encontrada.get('is_completed'):
            return Response({'error': 'Etapa já finalizada.'}, status=400)

        # Verifica dependências
        dependencias = etapa_encontrada.get('dependencies', [])
        steps_concluidas = {et.get('id') for et in steps if et.get('is_completed')}

        dependencias_pendentes = [dep for dep in dependencias if dep not in steps_concluidas]
        if dependencias_pendentes:
            return Response({
                'error': 'Etapa não pode ser concluída. Existem dependências pendentes.',
                'dependencias_pendentes': dependencias_pendentes
            }, status=400)

        # Marca como concluída
        etapa_encontrada['is_completed'] = True
        etapa_encontrada['completion_date'] = timezone.now().isoformat()
        etapa_encontrada['user_id'] = user_id
        etapa_encontrada['content_type_id'] = request.data.get('content_type_id')
        etapa_encontrada['object_id'] = request.data.get('object_id')

        process.steps = steps
        process.save()

        return Response({'status': 'etapa_concluida', 'step_id': etapa_id})


class StepNameViewSet(BaseModelViewSet):
    queryset = StepName.objects.all()
    serializer_class = StepNameSerializer
    

class ProcessStepCountListView(generics.ListAPIView):
    queryset = ProcessStepCount.objects.all()
    serializer_class = ProcessStepCountSerializer
    pagination_class = None
    
    
class ContentTypeEndpointViewSet(BaseModelViewSet):
    queryset = ContentTypeEndpoint.objects.all()
    serializer_class = ContentTypeEndpointSerializer