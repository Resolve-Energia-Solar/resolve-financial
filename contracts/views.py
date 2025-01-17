from datetime import datetime
import os
import requests
from rest_framework import status
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.utils import extract_data_from_pdf
from core.models import Attachment, DocumentType
from resolve_crm.models import ContractSubmission, Sale
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
import logging
from django.core.files.base import ContentFile


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


logger = logging.getLogger(__name__)

class ReciveContractInfomation(APIView):
    http_method_names = ['post']
    permission_classes = [AllowAny]

    def get_signature_data(self, data):
        return (
            data.get('event', {}).get('occurred_at', None),
            data.get('document', {}).get('key', None),
            data.get('document', {}).get('downloads', {}).get('signed_file_url', None),
            data.get('document', {}).get('status', None)
        )

    def fetch_document(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            raise ValueError("Erro ao baixar o arquivo do contrato.")
        return response.content

    def handle_contract_submission(self, document_key, signature_date, status):
        try:
            contract = ContractSubmission.objects.get(key_number=document_key)
            print('Contrato: ',contract)
            if status == 'closed':
                contract.status = 'A'
            elif status == 'canceled':
                contract.status = 'R'
            else:
                contract.status = 'P'
            contract.finished_at = signature_date
            
            contract.save()
            return contract
        except ContractSubmission.DoesNotExist:
            raise ValueError("Contrato não encontrado.")

    def save_signature_date(self, sale, signature_date):
        sale.signature_date = signature_date
        sale.save()

    def save_attachment(self, sale_id, file_content, document_type):
        content_type_model = ContentType.objects.get_for_model(Sale)
        
        sale = Sale.objects.get(id=sale_id)

        # Criar o ContentFile para encapsular o conteúdo do arquivo
        content_file = ContentFile(file_content, name=f"{document_type.name}-{sale.contract_number}.pdf")

        # Salvar o Attachment
        Attachment.objects.create(
            content_type=content_type_model,
            object_id=sale_id,
            file=content_file,
            document_type=document_type,
        )

    def post(self, request):
        with transaction.atomic():
            data = request.data
            try:
                signature_date, document_key, document_file, document_status = self.get_signature_data(data)
                
                signature_date = datetime.strptime(
                    signature_date.split('.')[0].replace('T', ' '), 
                    '%Y-%m-%d %H:%M:%S'
                ).date()
                
                if not all([signature_date, document_key, document_file]):
                    return Response({'message': 'Dados insuficientes no payload.'}, status=status.HTTP_400_BAD_REQUEST)


                contract = self.handle_contract_submission(document_key, signature_date, document_status)
                self.save_signature_date(contract.sale, signature_date)

                if document_status == 'closed':
                    document_content = self.fetch_document(document_file)
                    document_type = DocumentType.objects.get(id=os.environ.get('CONTENT_TYPE_DOCUMENT'))
                    self.save_attachment(contract.sale.id, document_content, document_type)

                return Response({'message': 'Contrato processado com sucesso.'}, status=status.HTTP_200_OK)
            except ValueError as e:
                logger.error(f"ValueError: {str(e)}")
                return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Exception: {str(e)}")
                return Response({'message': 'Erro ao processar o contrato.', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


