import os
from api.views import BaseModelViewSet
from .models import *
from .serializers import *
from datetime import datetime
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
import requests


class FinancierViewSet(BaseModelViewSet):
    queryset = Financier.objects.all()
    serializer_class = FinancierSerializer


class PaymentViewSet(BaseModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def perform_create(self, serializer):
        # Remover os campos que não pertencem ao modelo antes de salvar
        create_installments = self.request.data.pop('create_installments', False)
        
        # Converter 'installments_number' para um inteiro
        num_installments = int(self.request.data.pop('installments_number', 0) or 0)

        # Salvar o objeto Payment
        instance = serializer.save()

        # Criar parcelas se solicitado
        if create_installments and num_installments > 0:
            self.create_installments(instance, num_installments)

    def create_installments(self, payment, num_installments):
        # Garantir que due_date seja um objeto datetime
        if isinstance(payment.due_date, str):
            payment.due_date = datetime.strptime(payment.due_date, '%Y-%m-%d')

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


class FranchiseInstallmentViewSet(BaseModelViewSet):
    queryset = FranchiseInstallment.objects.all()
    serializer_class = FranchiseInstallmentSerializer

    # def perform_create(self, serializer):
    #     sale = serializer.validated_data['sale']
    #     # repass_percentage = serializer.validated_data['repass_percentage']
    #     remaining_percentage = FranchiseInstallment.remaining_percentage(sale)

    #     if repass_percentage > remaining_percentage:
    #         raise ValidationError(
    #             {"repass_percentage": f"Percentual restante para esta venda é {remaining_percentage}%. "
    #                                   f"Não é possível adicionar {repass_percentage}%."}
    #         )
    #     serializer.save()


class FinancialRecordViewSet(BaseModelViewSet):
    queryset = FinancialRecord.objects.all()
    serializer_class = FinancialRecordSerializer


class OmieIntegrationView(APIView):
    
    OMIE_API_URL = os.environ.get('OMIE_API_URL')
    OMIE_ACESSKEY = os.environ.get('OMIE_ACESSKEY')
    OMIE_ACESSTOKEN = os.environ.get('OMIE_ACESSTOKEN')
    
    def post(self, request):
        print("OmieIntegrationView GET request received")
        if not self.OMIE_API_URL or not self.OMIE_ACESSKEY or not self.OMIE_ACESSTOKEN:
            print("Environment variables not set")
            return Response({"error": "API URL, AcessKey and AccessToken not set in environment variables"}, status=500)
        
        omie_call = request.data.get('call', None)
        print(f"Received omie_call: {omie_call}")
        
        if omie_call == 'ListarDepartamentos':
            url = f"{self.OMIE_API_URL}/geral/departamentos/"
            headers = {
                'Content-Type': 'application/json',
            }
            data = {
                "call": "ListarDepartamentos",
                "app_key": self.OMIE_ACESSKEY,
                "app_secret": self.OMIE_ACESSTOKEN,
                "param": [{"pagina": 1, "registros_por_pagina": 999}]
            }
            print(f"Making request to Omie API at {url} with data: {data}")
            response = requests.post(url, headers=headers, json=data)
            print(f"Received response with status code: {response.status_code}")
            if response.status_code == 200:
                print("Request successful: fetching active departments")
                departments = response.json().get('departamentos', [])
                active_departments = [dept for dept in departments if dept.get('inativo') == 'N']
                return Response(active_departments)
            else:
                print("Failed to fetch data from Omie API")
                return Response({"error": "Failed to fetch data from Omie API"}, status=response.status_code)
            
        if omie_call == 'ListarCategorias':
            url = f"{self.OMIE_API_URL}/geral/categorias/"
            headers = {
                'Content-Type': 'application/json',
            }
            data = {
                "call": "ListarCategorias",
                "app_key": self.OMIE_ACESSKEY,
                "app_secret": self.OMIE_ACESSTOKEN,
                "param": [{"pagina": 1, "registros_por_pagina": 999}]
            }
            print(f"Making request to Omie API at {url} with data: {data}")
            response = requests.post(url, headers=headers, json=data)
            print(f"Received response with status code: {response.status_code}")
            if response.status_code == 200:
                print("Request successful: fetching active categories")
                categories = response.json().get('categoria_cadastro', [])
                active_categories = [cat for cat in categories if cat.get('totalizadora') == 'N' and cat.get('conta_inativa') == 'N']
                return Response(active_categories)
            else:
                print("Failed to fetch data from Omie API")
                return Response({"error": "Failed to fetch data from Omie API"}, status=response.status_code)
            
        if omie_call == 'ListarClientesResumido':
            
            filter = request.data.get('filter', None)
            
            if not filter:
                return Response({"error": "No filter parameter received"}, status=400)
            
            if filter.isdigit():
                filter = {
                    "cnpj_cpf": filter,
                    "inativo": "N"
                }
            else:
                filter = {
                    "razao_social": filter,
                    "inativo": "N"
                }
            
            url = f"{self.OMIE_API_URL}/geral/clientes/"
            headers = {
                'Content-Type': 'application/json',
            }
            data = {
                "call": "ListarClientesResumido",
                "app_key": self.OMIE_ACESSKEY,
                "app_secret": self.OMIE_ACESSTOKEN,
                "param": [{"clientesFiltro": [filter]}]
            }
            print(f"Making request to Omie API at {url} with data: {data}")
            response = requests.post(url, headers=headers, json=data)
            print(f"Received response with status code: {response.status_code}")
            if response.status_code == 200:
                print("Request successful: fetching active clients")
                clients = response.json().get('clientes_cadastro_resumido', [])
                return Response(clients)
            else:
                print("Failed to fetch data from Omie API")
                return Response({"error": "Failed to fetch data from Omie API"}, status=response.status_code)
        
        print("Invalid call parameter")
        return Response({"error": "Invalid call parameter"}, status=400)
