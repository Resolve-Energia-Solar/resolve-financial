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
import datetime
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from weasyprint import HTML

from logistics.models import ProjectMaterials
from resolve_crm.models import Project

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
        
        supported_lookups = {
            'ForeignKey': ['exact', 'in'],
            'BooleanField': ['exact', 'in'],
            'BigIntegerField': ['exact', 'in'],
            'PositiveIntegerField': ['exact', 'in'],
            'ManyToManyField': ['exact', 'in'],
            'CharField': ['icontains', 'in'],
            'TextField': ['icontains', 'in'],
            'DateField': ['range'],
            'DateTimeField': ['range'],
            'PositiveSmallIntegerField': ['exact', 'gte', 'lte'],
            'IntegerField': ['exact', 'gte', 'lte'],
            'DecimalField': ['exact', 'gte', 'lte'],
        }

        filter_fields = {}
        for field in list(model._meta.fields) + list(model._meta.many_to_many):
            field_type = field.get_internal_type()
            if field_type in supported_lookups and field_type not in exclude_field_types:
                filter_fields[field.name] = supported_lookups[field_type]
        return filter_fields


class GanttView(APIView):
    permission_classes = []

    def get(self, request):
        columns = [
            {"type": "string", "label": "Task ID"},
            {"type": "string", "label": "Task Name"},
            {"type": "date", "label": "Start Date"},
            {"type": "date", "label": "End Date"},
            {"type": "number", "label": "Duration"},
            {"type": "number", "label": "Percent Complete"},
            {"type": "string", "label": "Dependencies"},
        ]

        rows = [
            [
                "Research",
                "Find sources",
                datetime(2015, 1, 1).isoformat(),
                datetime(2015, 1, 5).isoformat(),
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



def generate_materials_pdf(request, project_id):
    try:
        project = get_object_or_404(Project, pk=project_id)
        print(f"Gerando PDF para o projeto: {project_id}")
        materials = ProjectMaterials.objects.filter(project=project, is_deleted=False)
        if not materials:
            return HttpResponse("Nenhum material encontrado para este projeto.", status=404)
        print(f"Materiais encontrados: {materials.count()}")
    except Project.DoesNotExist:
        return HttpResponse("Projeto não encontrado.", status=404)

    context = {
        'project': project,
        'materials': materials,
        'generation_date': datetime.datetime.now(),
    }

    html_string = render_to_string('materiais_projeto.html', context)

    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    
    filename = f"materiais-projeto-{project.project_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response