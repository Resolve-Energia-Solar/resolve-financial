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

from accounts.models import User
from resolve_crm.models import *
from resolve_crm.models import Task as LeadTask
from .serializers.accounts import UserSerializer
from .serializers.accounts import *
from .serializers.core import *
from .serializers.engineering import *
from .serializers.inspections import *
from .serializers.logistics import *
from .serializers.resolve_crm import *
from .utils import extract_data_from_pdf

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
    def list(self, request, *args, **kwargs):
        fields = request.query_params.get('fields')
        if fields:
            fields = fields.split(',')
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)

            # Filtrando os dados com base nos campos passados
            filtered_data = [
                {field: self._get_field_data(lead, field) for field in fields}
                for lead in serializer.data
            ]

            return Response(filtered_data)
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        fields = request.query_params.get('fields')
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        if fields:
            fields = fields.split(',')
            filtered_data = {field: self._get_field_data(serializer.data, field) for field in fields}
            return Response(filtered_data)

        return super().retrieve(request, *args, **kwargs)

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
        if name:
            queryset = queryset.filter(complete_name__icontains=name)
        return queryset
    
    
class LeadViewSet(BaseModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    

class TaskViewSet(BaseModelViewSet):
    queryset = LeadTask.objects.all()
    serializer_class = LeadTaskSerializer

    
class AttachmentViewSet(BaseModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer


class SquadViewSet(BaseModelViewSet):
    queryset = Squad.objects.all()
    serializer_class = SquadSerializer
    
    
class DepartmentViewSet(BaseModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer    
    

class BranchViewSet(BaseModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    

class MarketingCampaignViewSet(BaseModelViewSet):
    queryset = MarketingCampaign.objects.all()
    serializer_class = MarketingCampaignSerializer


class AddressViewSet(BaseModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer


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
