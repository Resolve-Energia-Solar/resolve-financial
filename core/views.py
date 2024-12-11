from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from api.views import BaseModelViewSet
from .models import *
from .serializers import *
from .pagination import AttachmentPagination
from django.core.exceptions import FieldDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils.text import capfirst


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
    queryset = ContentType.objects.all()
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

        if not content_type_id or not object_id:
            return Response({
                'message': 'content_type e object_id são obrigatórios.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Busca o ContentType ou retorna 404 se não encontrado
        content_type = get_object_or_404(ContentType, id=content_type_id)
        model_class = content_type.model_class()
        
        # Verifica se o model possui histórico
        if not hasattr(model_class, 'history'):
            return Response({
                'message': 'O modelo não possui histórico.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Busca o histórico para o objeto específico
            history = model_class.history.filter(id=object_id)
            if not history.exists():
                return Response({
                    'message': 'Histórico não encontrado para o objeto fornecido.'
                }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'message': 'Erro ao buscar o histórico.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                'message': 'Erro ao buscar o histórico.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Calcula as diferenças entre todas as versões consecutivas
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
                    # Obter o label do campo
                    try:
                        field_verbose = new_record._meta.get_field(field_name).verbose_name
                    except FieldDoesNotExist:
                        field_verbose = field_name  # Usa o nome do campo se o verbose_name não estiver definido
                    field_verbose = capfirst(field_verbose)
                    change_list.append({
                        'field': field_name,
                        'field_label': field_verbose,
                        'old': change.old,
                        'new': change.new
                    })
                changes.append({
                    'version_diff': f"{i + 1} -> {i + 2}",
                    'author': author_data,
                    'timestamp': new_record.history_date,
                    'history_type': new_record.history_type,
                    'changes': change_list
                })

        # Retornar somente as mudanças
        return Response({
            'changes': changes
        }, status=status.HTTP_200_OK)
