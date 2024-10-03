from venv import logger
from django.forms import ValidationError
from django.utils import timezone
import requests
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from accounts.models import *
from resolve_crm.models import *
from .serializers.accounts import *
from .serializers.resolve_crm import *
from .serializers.logistics import *
from .serializers.inspections import *
from .serializers.core import *
from .serializers.engineering import *
from resolve_crm.models import Task as LeadTask
from rest_framework.permissions import IsAuthenticated, AllowAny
from accounts.models import User
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers.accounts import UserSerializer

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
import logging
from django.urls import reverse

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

    def _get_field_data(self, obj, field):
        """Método auxiliar para obter dados de campos aninhados."""
        if '.' in field:
            keys = field.split('.')
            value = obj
            for key in keys:
                value = value.get(key, None)  # .get() para evitar erros se a chave não existir
            return value
        return obj.get(field, None)



class UserViewSet(BaseModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    
class AttachmentViewSet(BaseModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]


class SquadViewSet(BaseModelViewSet):
    queryset = Squad.objects.all()
    serializer_class = SquadSerializer
    permission_classes = [IsAuthenticated]
    
    
class DepartmentViewSet(BaseModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]    
    

class BranchViewSet(BaseModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]
    

class MarketingCampaignViewSet(BaseModelViewSet):
    queryset = MarketingCampaign.objects.all()
    serializer_class = MarketingCampaignSerializer
    permission_classes = [IsAuthenticated]


class AddressViewSet(BaseModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]


class RoleViewSet(BaseModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]


class PermissionViewSet(BaseModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]


class GroupViewSet(BaseModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]


class FinancierViewSet(BaseModelViewSet):
    queryset = Financier.objects.all()
    serializer_class = FinancierSerializer
    permission_classes = [IsAuthenticated]

class MaterialTypesViewSet(BaseModelViewSet):
    queryset = MaterialTypes.objects.all()
    serializer_class = MaterialTypesSerializer
    permission_classes = [IsAuthenticated]
    

class MaterialsViewSet(BaseModelViewSet):
    queryset = Materials.objects.all()
    serializer_class = MaterialsSerializer
    permission_classes = [IsAuthenticated]


class SolarEnergyKitViewSet(BaseModelViewSet):
    queryset = SolarEnergyKit.objects.all()
    serializer_class = SolarEnergyKitSerializer
    permission_classes = [IsAuthenticated]
    

class RoofTypeViewSet(BaseModelViewSet):
    queryset = RoofType.objects.all()
    serializer_class = RoofTypeSerializer

class EnergyCompanyViewSet(BaseModelViewSet):
    queryset = EnergyCompany.objects.all()
    serializer_class = EnergyCompanySerializer
    permission_classes = [IsAuthenticated]


class RequestsEnergyCompanyViewSet(BaseModelViewSet):
    queryset = RequestsEnergyCompany.objects.all()
    serializer_class = RequestsEnergyCompanySerializer
    permission_classes = [IsAuthenticated]


class CircuitBreakerViewSet(BaseModelViewSet):
    queryset = CircuitBreaker.objects.all()
    serializer_class = CircuitBreakerSerializer
    permission_classes = [IsAuthenticated]
    

class BoardViewSet(BaseModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]
    
    
class LeadTaskViewSet(BaseModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

 
class ColumnViewSet(BaseModelViewSet):
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer
    permission_classes = [IsAuthenticated]
    

class TaskTemplatesViewSet(BaseModelViewSet):
    queryset = TaskTemplates.objects.all()
    serializer_class = TaskTemplatesSerializer
    permission_classes = [IsAuthenticated]
    
    

class UnitsViewSet(BaseModelViewSet):
    queryset = Units.objects.all()
    serializer_class = UnitsSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]


class SaleViewSet(BaseModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    
from rest_framework.parsers import MultiPartParser
from .utils import extract_data_from_pdf


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
    