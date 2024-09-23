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


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    
class LeadViewSet(ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    

class TaskViewSet(ModelViewSet):
    queryset = LeadTask.objects.all()
    serializer_class = LeadTaskSerializer
    permission_classes = [IsAuthenticated]
    
    
class AttachmentViewSet(ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]


class SquadViewSet(ModelViewSet):
    queryset = Squad.objects.all()
    serializer_class = SquadSerializer
    permission_classes = [IsAuthenticated]
    
    
class DepartmentViewSet(ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]    
    

class BranchViewSet(ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]
    

class MarketingCampaignViewSet(ModelViewSet):
    queryset = MarketingCampaign.objects.all()
    serializer_class = MarketingCampaignSerializer
    permission_classes = [IsAuthenticated]


class AddressViewSet(ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]


class RoleViewSet(ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]


class PermissionViewSet(ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]


class FinancierViewSet(ModelViewSet):
    queryset = Financier.objects.all()
    serializer_class = FinancierSerializer
    permission_classes = [IsAuthenticated]

class MaterialTypesViewSet(ModelViewSet):
    queryset = MaterialTypes.objects.all()
    serializer_class = MaterialTypesSerializer
    permission_classes = [IsAuthenticated]
    

class MaterialsViewSet(ModelViewSet):
    queryset = Materials.objects.all()
    serializer_class = MaterialsSerializer
    permission_classes = [IsAuthenticated]


class SolarEnergyKitViewSet(ModelViewSet):
    queryset = SolarEnergyKit.objects.all()
    serializer_class = SolarEnergyKitSerializer
    permission_classes = [IsAuthenticated]
    

class RoofTypeViewSet(ModelViewSet):
    queryset = RoofType.objects.all()
    serializer_class = RoofTypeSerializer

class EnergyCompanyViewSet(ModelViewSet):
    queryset = EnergyCompany.objects.all()
    serializer_class = EnergyCompanySerializer
    permission_classes = [IsAuthenticated]


class RequestsEnergyCompanyViewSet(ModelViewSet):
    queryset = RequestsEnergyCompany.objects.all()
    serializer_class = RequestsEnergyCompanySerializer
    permission_classes = [IsAuthenticated]


class CircuitBreakerViewSet(ModelViewSet):
    queryset = CircuitBreaker.objects.all()
    serializer_class = CircuitBreakerSerializer
    permission_classes = [IsAuthenticated]
    

class BoardViewSet(ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]
    
    
class LeadTaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

 
class ColumnViewSet(ModelViewSet):
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer
    permission_classes = [IsAuthenticated]
    

class TaskTemplatesViewSet(ModelViewSet):
    queryset = TaskTemplates.objects.all()
    serializer_class = TaskTemplatesSerializer
    permission_classes = [IsAuthenticated]
    
    

class UnitsViewSet(ModelViewSet):
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
        url = "https://documentation.resolvenergiasolar.com/extract/fatura"
        headers = {
            'accept': 'application/json'
        }

        try:
            with unit.bill_file.open('rb') as f:
                files = {
                    'file': (unit.bill_file.name, f, 'application/pdf')
                }
                logger.info(f'Enviando fatura para a API externa para a unidade ID {unit.id}')
                response = requests.post(url, headers=headers, files=files, timeout=5)
                response.raise_for_status()
                external_data = response.json()

            unit.name = external_data.get('name', unit.name)
            unit.account_number = external_data.get('account', unit.account_number)
            unit.unit_number = external_data.get('uc', unit.unit_number)
            unit.type = external_data.get('type', unit.type)
            # unit.address = external_data.get('address', unit.address)
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


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]


class SaleViewSet(ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]