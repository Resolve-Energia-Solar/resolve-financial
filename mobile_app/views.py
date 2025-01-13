import logging
import os

import requests
from django.utils import timezone
from dotenv import load_dotenv
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from api.views import BaseModelViewSet
from core.serializers import AttachmentSerializer
from engineering.models import RequestsEnergyCompany
from field_services.models import Schedule
from mobile_app.serializers import *
from resolve_crm.models import Project, ProjectStep, Sale


# Carrega o .env
load_dotenv()


logger = logging.getLogger(__name__)


class CustomerLoginView(APIView):

    permission_classes = [AllowAny]
    http_method_names = ['post']

    def post(self, request):
        first_document = request.data.get('first_document')
        birth_date = request.data.get('birth_date')

        # Validar os campos recebidos
        if not first_document or not birth_date:
            return Response({
                'message': 'Documento e data de nascimento são obrigatórios.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.filter(first_document=first_document, birth_date=birth_date).order_by('-last_login').first()
        except User.DoesNotExist:
            return Response({
                'message': 'Usuário com esse documento e data de nascimento não encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Verificar se o usuário está ativo
        if not user.is_active:
            return Response({
                'message': 'Usuário inativo.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar se o usuário tem uma venda associada
        if not user.customer_sales.exists():
            return Response({
                'message': 'Cliente sem venda.'
            }, status=status.HTTP_403_FORBIDDEN)
        
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
            'last_login': last_login
        }, status=status.HTTP_200_OK)


class CustomerViewset(BaseModelViewSet):
    queryset = User.objects.filter(is_active=True, customer_sales__isnull=False).distinct()
    serializer_class = CustomerSerializer
    http_method_names = ['get']


class SaleViewset(BaseModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = MobileSaleSerializer
    http_method_names = ['get']


class ProjectViewset(BaseModelViewSet):
    queryset = Project.objects.all()
    serializer_class = MobileProjectSerializer
    http_method_names = ['get']


class DocumentationView(APIView):

    http_method_names = ['get']

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({
                'message': 'Projeto não encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)

        missing_documents = project.missing_documents
        attached_documents = project.attachments.all()
        
        attachments_data = AttachmentSerializer(attached_documents, many=True).data

        # Remover os campos 'content_type' e 'object_id' de cada anexo e ajustar 'document_type'
        for attachment in attachments_data:
            attachment.pop('content_type', None)
            attachment.pop('object_id', None)
            # Em 'document_type' e 'document_subtype', substituir por seu 'name'
            if 'document_type' in attachment and attachment['document_type'] and 'name' in attachment['document_type']:
                attachment['document_type'] = attachment['document_type']['name']
            if 'document_subtype' in attachment and attachment['document_subtype'] and 'name' in attachment['document_subtype']:
                attachment['document_subtype'] = attachment['document_subtype']['name']

        data = {
            'missing_documents': missing_documents,
            'attachments': attachments_data,
            'is_completed': project.is_documentation_completed
        }

        if not project.is_documentation_completed:
            try:
                deadline = project.project_steps.get(step__name='documentacao').deadline
            except ProjectStep.DoesNotExist:
                deadline = None
            data['deadline'] = deadline if deadline else None
        else:
            data['completion_date'] = project.documention_completion_date
            if project.start_date and project.documention_completion_date:
                data['duration'] = (project.documention_completion_date.date() - project.start_date).days
            else:
                logger.error('Erro ao calcular a duração da documentação do projeto %s', project.id)
                data['duration'] = None

        return Response(data, status=status.HTTP_200_OK)


class FinancialView(APIView):

    http_method_names = ['get']

    def get(self, request, sale_id):
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response({
                'message': 'Venda não encontrada.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        percentual_paid = (sale.total_paid * 100 / sale.total_value) if sale.total_value != 0 else 0

        data = {
            'total_paid': sale.total_paid,
            'percentual_paid': percentual_paid,
            'payment_status': sale.payment_status,
            'is_paid': sale.total_paid == sale.total_value,
            'is_completed': sale.payment_status != 'PENDENTE'
        }

        if sale.payment_status == 'PENDENTE':
            try:
                deadline = sale.projects.first().project_steps.get(step__name='financeiro').deadline
                data['deadline'] = deadline if deadline else None
            except:
                data['deadline'] = None
        else:
            data['completion_date'] = sale.financial_completion_date
            if sale.signature_date:
                data['duration'] = (sale.financial_completion_date.date() - sale.signature_date).days
            else:
                logger.error('Erro ao calcular a duração do financeiro da venda %s', sale.id)
                data['duration'] = None

        return Response(data, status=status.HTTP_200_OK)


class FieldServiceViewset(BaseModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = FieldServiceSerializer
    http_method_names = ['get']


class RequestsEnergyCompanyViewset(BaseModelViewSet):
    queryset = RequestsEnergyCompany.objects.all()
    serializer_class = RequestsEnergyCompanySerializer
    http_method_names = ['get']


SOLARZ_USERNAME = os.getenv('SOLARZ_USERNAME')
SOLARZ_PASSWORD = os.getenv('SOLARZ_PASSWORD')


class MonitoringListView(APIView):
    """
    Lista todos os contratos.
    """

    def get(self, request, *args, **kwargs):
        # URL e parâmetros da API externa
        url = "https://app.solarz.com.br/openApi/seller/plant/list/"
        params = {"page": 1, "pageSize": 20}
        auth = (SOLARZ_USERNAME, SOLARZ_PASSWORD)

        # Chamada para a API externa
        response = requests.post(url, json=params, auth=auth)

        if response.status_code == 200:
            queryset = response.json()

            # Garantir que queryset seja uma lista
            if not isinstance(queryset, list):
                return Response({"error": "Dados retornados não são uma lista"}, status=500)

            # Separar contratos por status
            alert_contracts = [
                contract for contract in queryset
                if isinstance(contract, dict) and contract.get('status', {}).get('status', '').upper() == 'ALERTA'
            ]
            unknown_contracts = [
                contract for contract in queryset
                if isinstance(contract, dict) and contract.get('status', {}).get('status', '').upper() == 'DESCONHECIDO'
            ]
            ok_contracts = [
                contract for contract in queryset
                if isinstance(contract, dict) and contract.get('status', {}).get('status', '').upper() == 'OK'
            ]

            return Response({
                "alert_contracts": alert_contracts,
                "unknown_contracts": unknown_contracts,
                "ok_contracts": ok_contracts,
            }, status=200)
        else:
            logger.error(f"Erro ao buscar contratos: {response.status_code} - {response.text}")
            return Response({"error": "Erro ao buscar contratos"}, status=400)


class MonitoringDetailView(APIView):
    """
    Retorna os detalhes do contrato para economia, consumo e produção de energia.
    """
    def get(self, request, plant_id):
        current_date = timezone.now()
        month = request.query_params.get("month", current_date.strftime("%m"))
        year = request.query_params.get("year", current_date.strftime("%Y"))

        auth = (SOLARZ_USERNAME, SOLARZ_PASSWORD)

        # URL para economia por mês
        economy_url = f"https://app.solarz.com.br/openApi/seller/plant/energy/plantId/{plant_id}/month/{year}-{month}"
        economy_response = requests.post(economy_url, auth=auth)

        # URL para produção de energia no período
        production_url = f"https://app.solarz.com.br/openApi/seller/plant/energy/plantId/{plant_id}/year/{year}"
        production_response = requests.post(production_url, auth=auth)

        if economy_response.status_code == 200 and production_response.status_code == 200:
            economy_data = economy_response.json()
            production_data = production_response.json()

            return Response({
                "economy": economy_data,
                "production": production_data,
            }, status=status.HTTP_200_OK)

        # Capturar erros específicos da API externa
        return Response({
            "error": "Erro ao buscar detalhes do contrato",
            "economy_status": economy_response.status_code,
            "economy_response": economy_response.text,
            "production_status": production_response.status_code,
            "production_response": production_response.text,
        }, status=status.HTTP_400_BAD_REQUEST)


class AttachDocumentView(APIView):
    
    http_method_names = ['post']

    def post(self, request):
        project_content_type = ContentType.objects.get_for_model(Project)
        data = request.data.copy()
        data['content_type_id'] = project_content_type.id
        serializer = AttachmentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class APIViewSet(BaseModelViewSet):
    queryset = API.objects.all()
    serializer_class = APISerializer


class DiscountViewSet(BaseModelViewSet):
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer


class ReelViewSet(BaseModelViewSet):
    queryset = Reel.objects.all()
    serializer_class = ReelSerializer


class MediaViewSet(BaseModelViewSet):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer


class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class SendNPSView(APIView):
    http_method_names = ['post']

    def post(self, request):
        project_id = request.data.get('project_id')
        step_id = request.data.get('step_id')
        nps_score = request.data.get('nps')

        # Debug prints
        print(f"Received project_id: {project_id}")
        print(f"Received step_id: {step_id}")
        print(f"Received nps_score: {nps_score}")

        # Validar os campos recebidos
        if not project_id or not step_id or not nps_score:
            return Response({
                'message': 'ID do projeto, ID do step e NPS são obrigatórios.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar o valor do NPS
        if not (1 <= nps_score <= 5):
            return Response({
                'message': 'O valor do NPS deve ser entre 1 e 5.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Salvar os dados no banco de dados
        try:
            project = Project.objects.get(id=project_id)
            step = ProjectStep.objects.filter(id=step_id, project=project).first()
            step.nps = nps_score
            step.save()
        except Project.DoesNotExist:
            print(f"Project with id {project_id} does not exist.")
            return Response({
                'message': 'Projeto não encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)
        except ProjectStep.DoesNotExist:
            print(f"Step with id {step_id} does not exist for project {project_id}.")
            return Response({
                'message': 'Step não encontrado para o projeto fornecido.'
            }, status=status.HTTP_404_NOT_FOUND)

        print(f"NPS score {nps_score} saved for project {project_id} and step {step_id}.")
        return Response({
            'message': 'NPS enviado com sucesso.'
        }, status=status.HTTP_201_CREATED)