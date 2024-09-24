from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from rest_framework.views import APIView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from .models import PaymentRequest
import os

import requests
from rest_framework import status
from .forms import PaymentRequestForm

from dotenv import load_dotenv
load_dotenv()


class PaymentRequestListView(UserPassesTestMixin, ListView):
    model = PaymentRequest
    template_name = 'financial/payment_requests_list.html'
    context_object_name = 'payment_requests'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.has_perm('financial.view_paymentrequest')
    
    """
    def get_queryset(self):
        return PaymentRequest.objects.filter(requester=self.request.user) | PaymentRequest.objects.filter(manager=self.request.user) | PaymentRequest.objects.filter(department=self.request.user.department) | PaymentRequest.objects.filter(supplier=self.request.user)
    """
    

class PaymentRequestDetailView(UserPassesTestMixin, DetailView):
    
    model = PaymentRequest
    template_name = 'financial/payment_requests_detail.html'
    
    def test_func(self):
        return self.request.user.has_perm('financial.view_paymentrequest') or self.request.user == self.get_object().requester or self.request.user == self.get_object().manager or self.request.user.department == self.get_object().department
    

class PaymentRequestCreateView(UserPassesTestMixin, CreateView):
        
        model = PaymentRequest
        form_class = PaymentRequestForm
        template_name = 'financial/payment_requests_form.html'
        success_url = reverse_lazy('financial:payment_requests_list')
        
        def test_func(self):
            return self.request.user.has_perm('financial.add_paymentrequest')


class PaymentRequestUpdateView(UserPassesTestMixin, UpdateView):
    
    model = PaymentRequest
    template_name = 'financial/payment_requests_form.html'
    fields = '__all__'
    success_url = reverse_lazy('financial:payment_requests_list')
    
    def test_func(self):
        return self.request.user.has_perm('financial.change_paymentrequest')


# Omie API

class OmieService:
    def __init__(self):
        self.base_url = os.getenv('OMIE_API_URL')
        self.omie_app_key = os.getenv('OMIE_ACESSKEY')
        self.omie_app_secret = os.getenv('OMIE_ACESSTOKEN')

    def listar_clientes(self, cnpj_cpf):
        data = {
            "call": "ListarClientes",
            "app_key": self.omie_app_key,
            "app_secret": self.omie_app_secret,
            "param": [
                {
                    "clientesFiltro": [
                        {
                            "cnpj_cpf": cnpj_cpf
                        }
                    ]
                }
            ]
        }
        
        headers = {
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(f'{self.base_url}/clientes/', json=data, headers=headers)
            response.raise_for_status()
            clientes = response.json().get('clientes_cadastro', [])
            fornecedores = [
                cliente for cliente in clientes
                if cliente.get('tags') and any(tag.get('tag') == 'Fornecedor' for tag in cliente.get('tags', []))
            ]
            return fornecedores
        except requests.RequestException as e:
            print(f'Erro na requisição Omie: {e}')
            return None
        
    def listar_categorias(self):
            pagina = 1
            registros_por_pagina = 300  # Ajuste conforme necessário
            categorias = []

            while True:
                data = {
                    "call": "ListarCategorias",
                    "app_key": self.omie_app_key,
                    "app_secret": self.omie_app_secret,
                    "param": [
                        {
                            "pagina": pagina,
                            "registros_por_pagina": registros_por_pagina
                        }
                    ]
                }

                headers = {
                    'Content-Type': 'application/json'
                }

                try:
                    response = requests.post(f'{self.base_url}/categorias/', json=data, headers=headers)
                    response.raise_for_status()
                    response_data = response.json()
                    categorias_pagina = response_data.get('categoria_cadastro', [])
                    total_de_paginas = response_data.get('total_de_paginas', 1)

                    # Filtrar apenas as categorias ativas (conta_inativa = 'N')
                    categorias_ativas = [
                        categoria for categoria in categorias_pagina
                        if categoria.get('conta_inativa') == 'N'
                    ]

                    categorias.extend(categorias_ativas)

                    if pagina >= total_de_paginas:
                        break

                    pagina += 1

                except requests.RequestException as e:
                    print(f'Erro na requisição Omie: {e}')
                    return None

            return categorias
        
    def create_supplier(self, cnpj_cpf, name):
        data = {
            "call": "IncluirCliente",
            "app_key": self.omie_app_key,
            "app_secret": self.omie_app_secret,
            "param": [
                {
                    "codigo_cliente_integracao": cnpj_cpf,
                    "cnpj_cpf": cnpj_cpf,
                    "razao_social": name,
                    "nome_fantasia": name,
                    "pessoa_fisica": "N" if len(cnpj_cpf) == 14 else "S",
                    "tags": [
                        {
                            "tag": "Fornecedor"
                        }
                    ]
                }
            ]
        }

        headers = {
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(f'{self.base_url}/clientes/', json=data, headers=headers)
            try:
                response_data = response.json()
            except ValueError:
                response_data = None

            if response.status_code != 200:
                # Extrair mensagem de erro específica
                if response_data:
                    if "faultstring" in response_data:
                        error_message = response_data["faultstring"]
                    elif "descricao_status" in response_data:
                        error_message = response_data["descricao_status"]
                    else:
                        error_message = response.text
                else:
                    error_message = response.reason
                return {"error": error_message}

            # Verificar se o Omie retornou um status de erro mesmo com status HTTP 200
            if response_data and response_data.get("codigo_status") != "0":
                error_message = response_data.get("descricao_status", "Erro desconhecido do Omie.")
                return {"error": error_message}

            return response_data

        except requests.RequestException as e:
            # Verificar se há uma resposta associada à exceção
            if e.response:
                try:
                    error_data = e.response.json()
                    if "faultstring" in error_data:
                        error_message = error_data["faultstring"]
                    elif "descricao_status" in error_data:
                        error_message = error_data["descricao_status"]
                    else:
                        error_message = e.response.text
                except ValueError:
                    error_message = e.response.text or str(e)
            else:
                error_message = str(e)
            return {"error": error_message}


class SuppliersListView(APIView):

    def get(self, request):
        query = request.GET.get('term', '').strip()
        if not query:
            return JsonResponse({'results': []}, status=status.HTTP_200_OK)

        omie_service = OmieService()
        suppliers = []

        # Remover caracteres especiais do CPF/CNPJ
        query_cnpj_cpf = query.replace('.', '').replace('-', '').replace('/', '')

        # Tentar buscar por CPF/CNPJ
        suppliers_cnpj = omie_service.listar_clientes(
            cnpj_cpf=query_cnpj_cpf
        )

        # Se encontrar fornecedores, usar esses resultados
        if suppliers_cnpj:
            suppliers = suppliers_cnpj

        if suppliers is None:
            return JsonResponse({"error": "Failed to fetch suppliers from Omie"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Construir a lista de resultados
        results = [
            {
                'id': supplier['codigo_cliente_omie'],
                'text': f"{supplier['nome_fantasia']} - {supplier['cnpj_cpf']}"
            }
            for supplier in suppliers
        ]

        return JsonResponse({
            'results': results
        }, status=status.HTTP_200_OK)


class CategoriesListView(APIView):

    def get(self, request):
        query = request.GET.get('term', '').strip().lower()

        omie_service = OmieService()
        categorias = omie_service.listar_categorias()

        if categorias is None:
            return JsonResponse({"error": "Failed to fetch categories from Omie"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Filtrar categorias com base no termo de busca
        if query:
            categorias_filtradas = [
                {
                    'id': categoria['codigo'],
                    'text': categoria['descricao']
                }
                for categoria in categorias
                if query in categoria.get('descricao', '').lower()
            ]
        else:
            categorias_filtradas = [
                {
                    'id': categoria['codigo'],
                    'text': categoria['descricao']
                }
                for categoria in categorias
            ]

        return JsonResponse({
            'results': categorias_filtradas
        }, status=status.HTTP_200_OK)


class CreateSupplierView(APIView):

    def post(self, request):
        omie_service = OmieService()

        if omie_service is None:
            return JsonResponse({"error": "Failed to initialize Omie service"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cpf_cnpj = request.data.get('cpfcnpj')
        name = request.data.get('name')

        if not cpf_cnpj or not name:
            return JsonResponse({"error": "Missing required fields: 'cpfcnpj' and 'name'."}, status=status.HTTP_400_BAD_REQUEST)

        response = omie_service.create_supplier(
            cnpj_cpf=cpf_cnpj,
            name=name
        )

        if "error" in response:
            return JsonResponse({"error": response["error"]}, status=status.HTTP_400_BAD_REQUEST)

        if response.get("codigo_status") != "0":
            return JsonResponse({
                "error": response.get("descricao_status", "Unknown error"),
                "codigo_cliente_integracao": response.get("codigo_cliente_integracao"),
                "codigo_cliente_omie": response.get("codigo_cliente_omie"),
                "codigo_status": response.get("codigo_status")
            }, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({
            'message': 'Fornecedor criado com sucesso!',
            'data': {
                'cnpj_cpf': cpf_cnpj,
                'name': name
            }
        }, status=status.HTTP_201_CREATED)
