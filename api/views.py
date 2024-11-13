import logging
import requests
from django.db.models import Q
from django.db import transaction
from rest_framework.exceptions import ValidationError
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
from api.serializers.financial import FinancierSerializer, PaymentSerializer, PaymentInstallmentSerializer
from financial.models import Payment, PaymentInstallment
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
from geopy.distance import geodesic
from django.db.models import Case, When, Value, FloatField, IntegerField
from rest_framework.decorators import action


logger = logging.getLogger(__name__)


class BaseModelViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = '__all__'
    http_method_names = ['get', 'post', 'put', 'delete', 'patch']

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

    @property
    def filterset_fields(self):
        model = self.get_queryset().model
        exclude_field_types = ['ImageField', 'FileField']
        supported_lookups = ['CharField', 'TextField', 'ForeignKey', 'DateField', 'DateTimeField', 'PositiveSmallIntegerField', 'IntegerField', 'DecimalField', 'ManyToManyField']
    
        filter_fields = {}
        for field in model._meta.fields + model._meta.many_to_many:
            if field.get_internal_type() in supported_lookups and field.get_internal_type() not in exclude_field_types:
                if field.get_internal_type() == 'ForeignKey':
                    filter_fields[field.name] = ['exact']
                elif field.get_internal_type() in ['CharField', 'TextField']:
                    filter_fields[field.name] = ['icontains', 'in']
                elif field.get_internal_type() in ['DateField', 'DateTimeField']:
                    filter_fields[field.name] = ['range']
                elif field.get_internal_type() in ['PositiveSmallIntegerField', 'IntegerField', 'DecimalField']:
                    filter_fields[field.name] = ['exact', 'gte', 'lte']
                elif field.get_internal_type() == 'ManyToManyField':
                    filter_fields[field.name] = ['exact', 'in']
        return filter_fields

# Accounts views

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


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post', 'put', 'delete', 'patch']
    

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

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
    
    
class EmployeeViewSet(ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    http_method_names = ['get', 'post', 'put', 'delete', 'patch']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        return Response(EmployeeSerializer(employee).data, status=status.HTTP_201_CREATED)


def calculate_distance(lat1, lon1, lat2, lon2):
    distance = geodesic((lat1, lon1), (lat2, lon2)).kilometers
    return distance
    
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
    
    
class DepartmentViewSet(BaseModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    

class BranchViewSet(BaseModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer


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


# CRM views

class OriginViewSet(BaseModelViewSet):
    queryset = Origin.objects.all()
    serializer_class = OriginSerializer


class LeadViewSet(BaseModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    filter_fields = '__all__'


class LeadTaskViewSet(BaseModelViewSet):
    queryset = LeadTask.objects.all()
    serializer_class = LeadTaskSerializer

    
class MarketingCampaignViewSet(BaseModelViewSet):
    queryset = MarketingCampaign.objects.all()
    serializer_class = MarketingCampaignSerializer


class ComercialProposalViewSet(BaseModelViewSet):
    queryset = ComercialProposal.objects.all()
    serializer_class = ComercialProposalSerializer


class SaleViewSet(BaseModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer


class ProjectViewSet(BaseModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class GeneratePreSaleView(APIView): 
    http_method_names = ['post']

    @transaction.atomic
    def post(self, request):
        lead_id = request.data.get('lead_id')
        products = request.data.get('products')
        # payment_data = request.data.get('payment')

        if not lead_id:
            return Response({'message': 'lead_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lead = Lead.objects.get(id=lead_id)
        except Lead.DoesNotExist:
            return Response({'message': 'Lead não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not lead.first_document:
            return Response({'message': 'Lead não possui documento cadastrado.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Criação ou recuperação do cliente usando Serializer
        customer = User.objects.filter(first_document=lead.first_document).first()
        if not customer:
            base_username = lead.name.split(' ')[0] + '.' + lead.name.split(' ')[-1]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user_data = {
                'complete_name': lead.name,
                'username': username,
                'first_name': lead.name.split(' ')[0],
                'last_name': lead.name.split(' ')[-1],
                'email': lead.contact_email,
                'addresses_ids': [address.id for address in lead.addresses.all()],
                'user_types_ids': [UserType.objects.get(id=2).id],
                'first_document': lead.first_document,
            }
            user_serializer = UserSerializer(data=user_data)
            if user_serializer.is_valid():
                customer = user_serializer.save()
            else:
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Atualiza o cliente existente com os dados do lead, se necessário
            user_serializer = UserSerializer(customer, data={
                'complete_name': lead.name,
                'email': lead.contact_email,
                'addresses': [address.id for address in lead.addresses.all()],
                'user_types': UserType.objects.get(id=2).id,
            }, partial=True)
            if user_serializer.is_valid():
                customer = user_serializer.save()
            else:
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        lead.customer = customer
        lead.save()

        products = []
        total_value = 0

        for product in products:
            # Verificar se é um novo produto ou um existente
            if 'id' not in product:
                # Criar novo produto
                product_serializer = ProductSerializer(data=product)
                if product_serializer.is_valid():
                    new_product = product_serializer.save()
                    products.append(new_product)

                    # Calcular o valor do produto com base nos materiais associados
                    product_value = self.calculate_product_value(new_product)
                    total_value += product_value
                else:
                    return Response(product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Capturar produto existente
                try:
                    existing_product = Product.objects.get(id=product['id'])
                    products.append(existing_product)

                    # Calcular o valor do produto com base nos materiais associados
                    product_value = self.calculate_product_value(existing_product)
                    total_value += product_value
                except Product.DoesNotExist:
                    return Response({'message': f'Produto com id {product["id"]} não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Criação da pré-venda usando Serializer
            sale_data = {
                'customer_id': customer.id,
                'lead_id': lead.id,
                'is_pre_sale': True,
                'status': 'P',
                'branch_id': lead.seller.employee.branch.id,
                'seller_id': lead.seller.id,
                'sales_supervisor_id': lead.seller.employee.user_manager.id if lead.seller.employee.user_manager else None,
                'sales_manager_id': lead.seller.employee.user_manager.employee.user_manager.id if lead.seller.employee.user_manager and lead.seller.employee.user_manager.employee.user_manager else None,
                'total_value': total_value,
            }
            sale_serializer = SaleSerializer(data=sale_data)
            if sale_serializer.is_valid():
                pre_sale = sale_serializer.save()
            else:
                return Response(sale_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Erro ao criar pré-venda: {str(e)}')
            return Response({'message': 'Erro ao criar pré-venda.', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Vinculação dos products ao projeto usando Serializer
        for product in products:
            project_data = {
                'sale_id': pre_sale.id,
                'status': 'P',
                'product_id': product.id,
                'addresses_ids': [address.id for address in lead.addresses.all()]
            }
            project_serializer = ProjectSerializer(data=project_data)
            if project_serializer.is_valid():
                project = project_serializer.save()
            else:
                return Response(project_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Criação do pagamento usando Serializer
        """
        payment_data['value'] = total_value
        payment_data['sale'] = pre_sale.id
        payment_serializer = PaymentSerializer(data=payment_data)
        if payment_serializer.is_valid():
            payment_serializer.save()
        else:
            return Response(payment_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        """

        return Response({
            'message': 'Cliente, products, pré-venda, projetos e ~~pagamentos~~ gerados com sucesso.',
            'pre_sale_id': pre_sale.id
        }, status=status.HTTP_200_OK)
    
        def calculate_product_value(product):
            """
            Função para calcular o valor total do produto com base no valor do próprio produto
            e dos materiais associados.
            """
            product_value = product.product_value

            # Somar o custo dos materiais associados ao produto
            associated_materials = ProductMaterials.objects.filter(product=product, is_deleted=False)
            for item in associated_materials:
                material_cost = item.material.price * item.amount
                product_value += material_cost

            return product_value


# Contracts views

class InformacaoFaturaAPIView(APIView):
    parser_classes = [MultiPartParser]
    http_method_names = ['post']
    permission_classes = [AllowAny]

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
        
    

class MaterialsViewSet(BaseModelViewSet):
    queryset = Materials.objects.all()
    serializer_class = MaterialsSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        material = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

# Inspections views

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

    # listar agendamentos por pessoa para timeline
    @action(detail=False, methods=['get'])
    def get_schedule_person(self, request):
        today = timezone.now().date()
        hours = [
            ('09:00', '10:30'),
            ('10:30', '12:00'),
            ('13:00', '14:30'),
            ('14:30', '16:00'),
            ('16:00', '17:30'),
            ('17:30', '19:00'), 
        ]

        schedules = Schedule.objects.filter(schedule_date=today).order_by('schedule_agent', 'schedule_start_time')
        agents = schedules.values_list('schedule_agent', flat=True).distinct()
        data = []

        for agent in agents:
            agent_schedules = schedules.filter(schedule_agent=agent)
            agent_data = {
                'agent': agent,
                'schedules': []
            }
            for start, end in hours:
                if agent_schedules.filter(schedule_start_time__lt=end, schedule_end_time__gt=start).exists():
                    agent_data['schedules'].append({
                        'start_time': start,
                        'end_time': end,
                        'status': 'Ocupado'
                    })
                else:
                    agent_data['schedules'].append({
                        'start_time': start,
                        'end_time': end,
                        'status': 'Livre'
                    })
            data.append(agent_data)
            
        return Response(data, status=status.HTTP_200_OK)
        


# Engineering views

class EnergyCompanyViewSet(BaseModelViewSet):
    queryset = EnergyCompany.objects.all()
    serializer_class = EnergyCompanySerializer


class RequestsEnergyCompanyViewSet(BaseModelViewSet):
    queryset = RequestsEnergyCompany.objects.all()
    serializer_class = RequestsEnergyCompanySerializer
    

class UnitsViewSet(BaseModelViewSet):
    queryset = Units.objects.all()
    serializer_class = UnitsSerializer
    
    # def perform_create(self, serializer):
    #     instance = serializer.save()
    #     if 'bill_file' in self.request.FILES:
    #         self.process_bill_file(instance)

    # def perform_update(self, serializer):
    #     instance = serializer.save()
    #     if 'bill_file' in self.request.FILES:
    #         self.process_bill_file(instance)

    # def process_bill_file(self, unit):
    #     # Resolve a URL para o endpoint API
    #     # Garante que a URL é absoluta (pode ser ajustado para usar seu domínio se necessário)
    #     url = self.request.build_absolute_uri(reverse('api:invoice_information'))

    #     headers = {
    #         'accept': 'application/json'
    #     }

    #     try:
    #         # Abre o arquivo da unidade
    #         with unit.bill_file.open('rb') as f:
    #             files = {
    #                 'bill_file': (unit.bill_file.name, f, 'application/pdf')
    #             }
    #             logger.info(f'Enviando fatura para a API externa para a unidade ID {unit.id}')
                
    #             # Faz a requisição POST para a API
    #             response = requests.post(url, headers=headers, files=files, timeout=5)
    #             response.raise_for_status()  # Lança exceção em caso de status de erro HTTP

    #             # Pega os dados retornados pela API
    #             external_data = response.json()

    #         #nao deixar colocar repetido
    #         # Atualiza os dados da unidade com base nos dados da API
    #         unit.name = external_data.get('name', unit.name)
    #         unit.account_number = external_data.get('uc', unit.unit_number)
    #         unit.unit_number = external_data.get('account', unit.account_number)
    #         unit.type = external_data.get('type', unit.type)
    #         # unit.address = external_data.get('address', unit.address)  # Se você precisar adicionar o campo de endereço
    #         unit.save()

    #         logger.info(f'Dados da API externa atualizados para a unidade ID {unit.id}')

    #     except requests.exceptions.Timeout:
    #         logger.error(f'Timeout ao enviar fatura para a API externa para a unidade ID {unit.id}')
    #         raise ValidationError({'error': 'Timeout ao processar o arquivo da fatura.'})
    #     except requests.exceptions.HTTPError as http_err:
    #         logger.error(f'Erro HTTP ao enviar fatura para a API externa para a unidade ID {unit.id}: {str(http_err)}')
    #         raise ValidationError({'error': 'Erro ao processar o arquivo da fatura.'})
    #     except requests.exceptions.RequestException as req_err:
    #         logger.error(f'Erro na requisição ao enviar fatura para a API externa para a unidade ID {unit.id}: {str(req_err)}')
    #         raise ValidationError({'error': 'Erro ao processar o arquivo da fatura.'})
    #     except Exception as e:
    #         logger.error(f'Erro inesperado ao processar fatura para a unidade ID {unit.id}: {str(e)}')
    #         raise ValidationError({'error': 'Erro ao processar o arquivo da fatura.'})


# Core views

class AttachmentViewSet(BaseModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer


class ContentTypeViewSet(BaseModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    http_method_names = ['get']


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

 
# Financial views

class FinancierViewSet(BaseModelViewSet):
    queryset = Financier.objects.all()
    serializer_class = FinancierSerializer


class PaymentViewSet(BaseModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        create_installments = self.request.data.get('create_installments', False)
        if create_installments:
            self.create_installments(instance)

    def create_installments(self, payment):
        num_installments = self.request.data.get('installments_number', False)
        installment_amount = payment.value / num_installments

        for i in range(num_installments):
            PaymentInstallment.objects.create(
                payment=payment,
                installment_value=installment_amount,
                due_date=payment.due_date + timezone.timedelta(days=30 * i),
                installment_number=i + 1
            )


class PaymentInstallmentViewSet(BaseModelViewSet):
    queryset = PaymentInstallment.objects.all()
    serializer_class = PaymentInstallmentSerializer


# History views

class HistoryView(APIView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        content_type_id = request.data.get('content_type')
        object_id = request.data.get('object_id')

        if not content_type_id or not object_id:
            return Response({
                'message': 'content_type e object_id são obrigatórios.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            content_type = ContentType.objects.get(id=content_type_id)
        except ContentType.DoesNotExist:
            return Response({
                'message': 'ContentType não encontrado.'
            }, status=status.HTTP_400_BAD_REQUEST)

        history = content_type.model_class().history.filter(id=object_id)

        return Response({
            'history': list(history.values())
        }, status=status.HTTP_200_OK)
 


class SupplyAdequanceViewSet(BaseModelViewSet):
    queryset = SupplyAdequance.objects.all()
    serializer_class = SupplyAdequanceSerializer


class ResquestTypeViewSet(BaseModelViewSet):
    queryset = ResquestType.objects.all()
    serializer_class = ResquestTypeSerializer
    
    
class SituationEnergyCompanyViewSet(BaseModelViewSet):
    queryset = SituationEnergyCompany.objects.all()
    serializer_class = SituationEnergyCompanySerializer
    
    