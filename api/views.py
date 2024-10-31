import logging
import requests
from django.db.models import Q
from django.forms import ValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.utils.dateparse import parse_datetime, parse_time
from accounts.models import User
from inspections.models import Category, Service
from resolve_crm.models import *
from resolve_crm.models import Task as LeadTask
from .serializers.accounts import UserSerializer
from .serializers.accounts import *
from .serializers.core import *
from .serializers.engineering import *
from .serializers.logistics import *
from .serializers.resolve_crm import *
from .serializers.inspections import *
from .utils import extract_data_from_pdf
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from .filters import GenericFilter
from geopy.distance import geodesic
from django.db.models import Case, When, Value, FloatField, IntegerField


logger = logging.getLogger(__name__)


class UserLoginView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        # Validar os campos recebidos
        if not email or not password:
            return Response({
                'message': 'Email e senha são obrigatórios.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'message': 'Usuário com esse email não encontrado.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar se o usuário está ativo
        if not user.is_active:
            return Response({
                'message': 'Usuário inativo.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar senha
        if not user.check_password(password):
            return Response({
                'message': 'Senha incorreta.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        last_login = user.last_login
        
        # Gerar e retornar os tokens JWT
        refresh = RefreshToken.for_user(user)
        
        # Atualizar o último login do usuário
        user.last_login = timezone.now()
        user.save()

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'id': user.id,
            'username': user.username,
            'last_login': last_login,
        }, status=status.HTTP_200_OK)


class UserTokenRefreshView(TokenRefreshView):
    http_method_names = ['post']
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class BaseModelViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = '__all__'

    def get_filterset_class(self):
        return GenericFilter

    def get_filterset_kwargs(self):
        kwargs = super().get_filterset_kwargs()
        kwargs['model'] = self.get_queryset().model
        return kwargs

    def list(self, request, *args, **kwargs):
        fields = request.query_params.get('fields')
        
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.paginate_queryset(queryset)

        if fields:
            fields = fields.split(',')
            serializer = self.get_serializer(queryset, many=True)
            filtered_data = [
                {field: self._get_field_data(item, field) for field in fields}
                for item in serializer.data
            ]
            return self.get_paginated_response(filtered_data)

        serializer = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        fields = request.query_params.get('fields')
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        if fields:
            fields = fields.split(',')
            filtered_data = {field: self._get_field_data(serializer.data, field) for field in fields}
            return Response(filtered_data, status=status.HTTP_200_OK)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_field_data(self, obj, field):
        """Método auxiliar para obter dados de campos aninhados."""
        if '.' in field:
            keys = field.split('.')
            value = obj
            for key in keys:
                if isinstance(value, list):
                    value = [item.get(key, None) for item in value if isinstance(item, dict)]
                elif isinstance(value, dict):
                    value = value.get(key, None)
                else:
                    return None
            return value
        return obj.get(field, None)
    
    
class UserViewSet(BaseModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        user_type = self.request.query_params.get('type')
        email = self.request.query_params.get('email')
        phone = self.request.query_params.get('phone')
        branch = self.request.query_params.get('branch')
        department = self.request.query_params.get('department')
        role = self.request.query_params.get('role')
        person_type = self.request.query_params.get('person_type')
        first_document = self.request.query_params.get('first_document')
        second_document = self.request.query_params.get('second_document')
        category = self.request.query_params.get('category')
        date = self.request.query_params.get('date')
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')

        if name:
            queryset = queryset.filter(complete_name__icontains=name)
        if user_type:
            queryset = queryset.filter(user_types__name=user_type)
        if email:
            queryset = queryset.filter(email__icontains=email)
        if phone:
            queryset = queryset.filter(phone__number__icontains=phone)
        if branch:
            queryset = queryset.filter(branch__name__icontains=branch)
        if department:
            queryset = queryset.filter(department__name__icontains=department)
        if role:
            queryset = queryset.filter(role__name__icontains=role)
        if person_type:
            queryset = queryset.filter(person_type=person_type)
        if first_document:
            queryset = queryset.filter(first_document__icontains=first_document)
        if second_document:
            queryset = queryset.filter(second_document__icontains=second_Jdocument)
        if category:
            queryset = queryset.filter(id__in=Category.objects.get(id=category).members.values_list('id', flat=True))

            if date and start_time and end_time:
                overlapping_schedules = Schedule.objects.filter(
                    schedule_date=date,
                    schedule_start_time__lt=parse_time(end_time),
                    schedule_end_time__gt=parse_time(start_time)
                ).values_list('schedule_agent_id', flat=True)

                queryset = queryset.exclude(id__in=overlapping_schedules)

                if latitude and longitude:
                    latitude = float(latitude)
                    longitude = float(longitude)

                    users_distance = []
                    for user in queryset:
                        last_schedule = Schedule.objects.filter(
                            schedule_agent=user,
                            schedule_date=date
                        ).order_by('-schedule_end_time').first()

                        user.distance = (
                            calculate_distance(latitude, longitude, last_schedule.latitude, last_schedule.longitude)
                            if last_schedule else None
                        )

                        users_distance.append((user, user.distance))

                        daily_schedules_count = Schedule.objects.filter(
                            schedule_agent=user,
                            schedule_date=date
                        ).count()
                        user.daily_schedules_count = daily_schedules_count

                    ordered_users = sorted(users_distance, key=lambda x: (x[1] is None, x[1]))
                    ordered_ids = [user[0].id for user in ordered_users]

                    queryset = queryset.filter(id__in=ordered_ids).annotate(
                        distance=Case(
                            *[When(id=user.id, then=Value(user.distance)) for user, _ in users_distance],
                            default=Value(None),  
                            output_field=FloatField()  
                        ),
                        daily_schedules_count=Case(
                            *[When(id=user.id, then=Value(user.daily_schedules_count)) for user in queryset],
                            default=Value(0),
                            output_field=IntegerField()  
                        )
                    ).order_by(
                        Case(
                            *[When(id=user_id, then=pos) for pos, user_id in enumerate(ordered_ids)]
                        )
                    )
        return queryset
    

def calculate_distance(lat1, lon1, lat2, lon2):
    distance = geodesic((lat1, lon1), (lat2, lon2)).kilometers
    formatted_distance = '{:.2f}'.format(distance)
    return formatted_distance
    
class LeadViewSet(BaseModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        type = self.request.query_params.get('type')
        first_document = self.request.query_params.get('first_document')
        second_document = self.request.query_params.get('second_document')
        contact_email = self.request.query_params.get('contact_email')
        phone = self.request.query_params.get('phone')
        origin = self.request.query_params.get('origin')
        seller = self.request.query_params.get('seller')
        sdr = self.request.query_params.get('sdr')
        funnel = self.request.query_params.get('funnel')
        column = self.request.query_params.get('column')

        if name:
            queryset = queryset.filter(name__icontains=name)
        if type:
            queryset = queryset.filter(type=type)
        if first_document:
            queryset = queryset.filter(first_document__icontains=first_document)
        if second_document:
            queryset = queryset.filter(second_document__icontains=second_document)
        if contact_email:
            queryset = queryset.filter(contact_email__icontains=contact_email)
        if phone:
            queryset = queryset.filter(phone__icontains=phone)
        if origin:
            queryset = queryset.filter(origin__icontains=origin)
        if seller:
            queryset = queryset.filter(seller__name__icontains=seller)
        if sdr:
            queryset = queryset.filter(sdr__name__icontains=sdr)
        if funnel:
            queryset = queryset.filter(funnel=funnel)
        if column:
            queryset = queryset.filter(column__id=column)

        return queryset
    

class TaskViewSet(BaseModelViewSet):
    queryset = LeadTask.objects.all()
    serializer_class = LeadTaskSerializer

    
class AttachmentViewSet(BaseModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        object_id = self.request.query_params.get('object_id')
        content_type = self.request.query_params.get('content_type_id')

        if object_id:
            queryset = queryset.filter(object_id=object_id)
        if content_type:
            queryset = queryset.filter(content_type=content_type)

        return queryset


class SquadViewSet(BaseModelViewSet):
    queryset = Squad.objects.all()
    serializer_class = SquadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset
    
    
class DepartmentViewSet(BaseModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset
    

class BranchViewSet(BaseModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset
    

class MarketingCampaignViewSet(BaseModelViewSet):
    queryset = MarketingCampaign.objects.all()
    serializer_class = MarketingCampaignSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class AddressViewSet(BaseModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('q')

        if search:
            queryset = queryset.filter(
                Q(zip_code__icontains=search) |
                Q(country__icontains=search) |
                Q(state__icontains=search) |
                Q(city__icontains=search) |
                Q(neighborhood__icontains=search) |
                Q(street__icontains=search) |
                Q(number__icontains=search) |
                Q(complement__icontains=search)
            )

        return queryset


class RoleViewSet(BaseModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class PermissionViewSet(BaseModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer


class GroupViewSet(BaseModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class FinancierViewSet(BaseModelViewSet):
    queryset = Financier.objects.all()
    serializer_class = FinancierSerializer


class MaterialTypesViewSet(BaseModelViewSet):
    queryset = MaterialTypes.objects.all()
    serializer_class = MaterialTypesSerializer
    

class MaterialsViewSet(BaseModelViewSet):
    queryset = Materials.objects.all()
    serializer_class = MaterialsSerializer


class SolarEnergyKitViewSet(BaseModelViewSet):
    queryset = SolarEnergyKit.objects.all()
    serializer_class = SolarEnergyKitSerializer
    

class RoofTypeViewSet(BaseModelViewSet):
    queryset = RoofType.objects.all()
    serializer_class = RoofTypeSerializer

class CategoryViewSet(BaseModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset
    
class DeadlineViewSet(BaseModelViewSet):
    queryset = Deadline.objects.all()
    serializer_class = DeadlineSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

class ServiceViewSet(BaseModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

class FormsViewSet(BaseModelViewSet):
    queryset = Forms.objects.all()
    serializer_class = FormsSerializer

class AnswerViewSet(BaseModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer

class ScheduleViewSet(BaseModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        project = self.request.query_params.get('project')
        service = self.request.query_params.get('service')
        schedule_agent = self.request.query_params.get('schedule_agent')

        if project:
            queryset = queryset.filter(project__id=project)
        if service:
            queryset = queryset.filter(service__id=service)
        if schedule_agent:
            queryset = queryset.filter(schedule_agent__id=schedule_agent)

        return queryset

class EnergyCompanyViewSet(BaseModelViewSet):
    queryset = EnergyCompany.objects.all()
    serializer_class = EnergyCompanySerializer


class RequestsEnergyCompanyViewSet(BaseModelViewSet):
    queryset = RequestsEnergyCompany.objects.all()
    serializer_class = RequestsEnergyCompanySerializer


class CircuitBreakerViewSet(BaseModelViewSet):
    queryset = CircuitBreaker.objects.all()
    serializer_class = CircuitBreakerSerializer
    

class BoardViewSet(BaseModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    
    
class LeadTaskViewSet(BaseModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

 
class ColumnViewSet(BaseModelViewSet):
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer
    

class TaskTemplatesViewSet(BaseModelViewSet):
    queryset = TaskTemplates.objects.all()
    serializer_class = TaskTemplatesSerializer


class UnitsViewSet(BaseModelViewSet):
    queryset = Units.objects.all()
    serializer_class = UnitsSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        if 'bill_file' in self.request.FILES:
            self.process_bill_file(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        if 'bill_file' in self.request.FILES:
            self.process_bill_file(instance)

    def process_bill_file(self, unit):
        # Resolve a URL para o endpoint API
        # Garante que a URL é absoluta (pode ser ajustado para usar seu domínio se necessário)
        url = self.request.build_absolute_uri(reverse('api:invoice_information'))

        headers = {
            'accept': 'application/json'
        }

        try:
            # Abre o arquivo da unidade
            with unit.bill_file.open('rb') as f:
                files = {
                    'bill_file': (unit.bill_file.name, f, 'application/pdf')
                }
                logger.info(f'Enviando fatura para a API externa para a unidade ID {unit.id}')
                
                # Faz a requisição POST para a API
                response = requests.post(url, headers=headers, files=files, timeout=5)
                response.raise_for_status()  # Lança exceção em caso de status de erro HTTP

                # Pega os dados retornados pela API
                external_data = response.json()

            # Atualiza os dados da unidade com base nos dados da API
            unit.name = external_data.get('name', unit.name)
            unit.account_number = external_data.get('uc', unit.unit_number)
            unit.unit_number = external_data.get('account', unit.account_number)
            unit.type = external_data.get('type', unit.type)
            # unit.address = external_data.get('address', unit.address)  # Se você precisar adicionar o campo de endereço
            unit.save()

            logger.info(f'Dados da API externa atualizados para a unidade ID {unit.id}')

        except requests.exceptions.Timeout:
            logger.error(f'Timeout ao enviar fatura para a API externa para a unidade ID {unit.id}')
            raise ValidationError({'error': 'Timeout ao processar o arquivo da fatura.'})
        except requests.exceptions.HTTPError as http_err:
            logger.error(f'Erro HTTP ao enviar fatura para a API externa para a unidade ID {unit.id}: {str(http_err)}')
            raise ValidationError({'error': 'Erro ao processar o arquivo da fatura.'})
        except requests.exceptions.RequestException as req_err:
            logger.error(f'Erro na requisição ao enviar fatura para a API externa para a unidade ID {unit.id}: {str(req_err)}')
            raise ValidationError({'error': 'Erro ao processar o arquivo da fatura.'})
        except Exception as e:
            logger.error(f'Erro inesperado ao processar fatura para a unidade ID {unit.id}: {str(e)}')
            raise ValidationError({'error': 'Erro ao processar o arquivo da fatura.'})


class ProjectViewSet(BaseModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class SaleViewSet(BaseModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('q')

        if search:
            queryset = queryset.filter(
                Q(customer__first_document__icontains=search) |
                Q(customer__second_document__icontains=search) |
                Q(customer__complete_name__icontains=search) |
                Q(contract_number__icontains=search)
            )

        return queryset
    

class InformacaoFaturaAPIView(APIView):
    parser_classes = [MultiPartParser]
    http_method_names = ['post']

    def post(self, request):
        if 'bill_file' not in request.FILES:
            return Response({
                'message': 'Arquivo da fatura é obrigatório.'
            }, status=status.HTTP_400_BAD_REQUEST)

        bill_file = request.FILES['bill_file']

        try:
            data = extract_data_from_pdf(bill_file)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'message': 'Erro ao processar a fatura.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ContentTypeViewSet(BaseModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    http_method_names = ['get']
