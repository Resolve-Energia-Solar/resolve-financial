from django.utils.functional import cached_property
from datetime import datetime
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import DjangoModelPermissions, AllowAny
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from api.pagination import CustomPagination
from api.task import processar_contrato


class BaseModelViewSet(ModelViewSet):
    permission_classes = [DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = '__all__'
    http_method_names = ['get', 'post', 'put', 'delete', 'patch']
    pagination_class = CustomPagination

    @cached_property
    def filterset_fields(self):
        model = self.get_queryset().model
        exclude_field_types = ['ImageField', 'FileField']
        supported_lookups = [
            'CharField', 'TextField', 'ForeignKey', 'DateField',
            'DateTimeField', 'PositiveSmallIntegerField', 'IntegerField',
            'DecimalField', 'ManyToManyField', 'BooleanField', 'BigIntegerField'
        ]

        filter_fields = {}
        for field in model._meta.fields + model._meta.many_to_many:
            if field.get_internal_type() in supported_lookups and field.get_internal_type() not in exclude_field_types:
                if field.get_internal_type() in ['ForeignKey', 'BooleanField', 'BigIntegerField', 'PositiveIntegerField', 'ManyToManyField']:
                    filter_fields[field.name] = ['exact', 'in']
                elif field.get_internal_type() in ['CharField', 'TextField']:
                    filter_fields[field.name] = ['icontains', 'in']
                elif field.get_internal_type() in ['DateField', 'DateTimeField']:
                    filter_fields[field.name] = ['range']
                elif field.get_internal_type() in ['PositiveSmallIntegerField', 'IntegerField', 'DecimalField']:
                    filter_fields[field.name] = ['exact', 'gte', 'lte']
        return filter_fields
    
    
class ContratoView(APIView):
    def post(self, request):
        dados_contrato = request.data
        
        # Pegue o token do frontend (geralmente enviado no header ou no corpo da requisição)
        token = request.headers.get("Authorization")  # Ou `request.data['token']` se enviado no body

        # Prepare os headers com o token recebido
        headers = {"Authorization": token}

        # Envie os dados para o Celery, incluindo o token
        processar_contrato.delay(dados_contrato, token)
        
        return Response({"message": "Contrato enviado para processamento"}, status=status.HTTP_202_ACCEPTED)


class GanttView(APIView):
    permission_classes = []  # Remove authentication requirement

    def get(self, request):
        # Colunas definidas no formato esperado
        columns = [
            {"type": "string", "label": "Task ID"},
            {"type": "string", "label": "Task Name"},
            {"type": "date", "label": "Start Date"},
            {"type": "date", "label": "End Date"},
            {"type": "number", "label": "Duration"},
            {"type": "number", "label": "Percent Complete"},
            {"type": "string", "label": "Dependencies"},
        ]

        # Dados das linhas no formato especificado
        rows = [
            [
                "Research",
                "Find sources",
                datetime(2015, 1, 1).isoformat(),  # Envia a data como string ISO
                datetime(2015, 1, 5).isoformat(),  # Envia a data como string ISO
                None,
                100,
                None,
            ],
            [
                "Write",
                "Write paper",
                None,
                datetime(2015, 1, 9).isoformat(),
                3 * 24 * 60 * 60 * 1000,  # Duração em milissegundos
                25,
                "Research,Outline",
            ],
        ]

        # Retorna no formato {columns, rows}
        data = {"columns": columns, "rows": rows}

        return Response(data)


class StatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "OK"}, status=status.HTTP_200_OK)
