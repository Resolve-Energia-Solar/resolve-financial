import os
import random
import string
import logging
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import AppsheetUser, PaymentRequest
from .forms import PaymentRequestForm


load_dotenv()
logger = logging.getLogger(__name__)


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
    success_url = reverse_lazy('financial:payment_request_list')
    
    def test_func(self):
        return self.request.user.has_perm('financial.add_paymentrequest')
    
    def calc_due_date(self, service_date, amount):
        if amount <= 3000:
            due_date = service_date + timedelta(days=2)
        elif amount <= 6000:
            due_date = service_date + timedelta(days=3)
        elif amount <= 10000:
            due_date = service_date + timedelta(days=4)
        elif amount <= 20000:
            due_date = service_date + timedelta(days=10)
        else:
            due_date = service_date + timedelta(days=15)
        return due_date
        
    def form_valid(self, form):
        try:
            appsheet_user = AppsheetUser.objects.get(email=self.request.user.email)
        except AppsheetUser.DoesNotExist:
            form.add_error(None, "Usuário não encontrado.")
            return self.form_invalid(form)

        form.instance.id = ''.join(random.choices(string.ascii_letters + string.digits, k=8)).lower()
        now = datetime.now()
        form.instance.protocol = (
            f"{now.strftime('%H%M%S')}"
            f"{now.year}"
            f"{now.strftime('%m')}"
            f"{now.strftime('%d')}"
        )
        form.instance.requester = appsheet_user
        form.instance.department = appsheet_user.user_department
        form.instance.manager = appsheet_user.user_manager
        form.instance.due_date = self.calc_due_date(form.instance.service_date, form.instance.amount)
        form.instance.requesting_status = 'Solicitado'
        form.instance.manager_status = 'Pendente'
        form.instance.financial_status = 'Pendente'
        form.instance.created_at = now

        response = super().form_valid(form)

        # Obter supplier_id, supplier_name e supplier_cpf
        supplier_id = form.cleaned_data.get('id_supplier')
        supplier_name = form.cleaned_data.get('supplier_name')
        supplier_cpf = form.cleaned_data.get('supplier_cpf')

        # Validar os campos do fornecedor
        if not all([supplier_id, supplier_name, supplier_cpf]):
            logger.warning("Informações do fornecedor incompletas.")
            # Opcional: Adicionar mensagens de erro ou tomar outras ações
            messages.warning(self.request, "Informações do fornecedor estão incompletas.")

        # Preparar o corpo da requisição para o webhook
        webhook_body = {
            "id": form.instance.id,
            "manager_email": form.instance.manager.email,
            "description": (
                f"Solicitação de Autorização de Pagamento - nº {form.instance.protocol}\n"
                f"Criada em {form.instance.created_at.strftime('%d/%m/%Y %H:%M:%S')} por {form.instance.requester.name} "
                f"do setor {form.instance.department.name}.\n"
                f"Valor da solicitação: {form.instance.amount}.\n"
                f"Descrição: {form.instance.description}.\n"
                f"Fornecedor: {supplier_name} ({supplier_cpf})"
            )
        }

        # Enviar a requisição POST para o webhook com tratamento de erros
        webhook_url = "https://prod-15.brazilsouth.logic.azure.com:443/workflows/378509394cc24a5d9568d886b8aaa7cd/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=aE_oGAJAt-2bdt8YXcus_tksAl8BHweHnGj58i6DlvI"
        headers = {'Content-Type': 'application/json'}

        try:
            response_webhook = requests.post(webhook_url, json=webhook_body, headers=headers)
            response_webhook.raise_for_status()  # Levanta uma exceção para status de erro HTTP
            logger.info(f"Webhook enviado com sucesso para {webhook_url}. Resposta: {response_webhook.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar para o webhook: {e}")
            # Opcional: Adicionar mensagens de erro para o usuário ou tomar outras ações
            messages.error(self.request, "Falha ao enviar dados para o webhook. Por favor, tente novamente mais tarde.")

        return response



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
        self.logger = logging.getLogger(__name__)

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
            # Endpoint correto para clientes
            response = requests.post(f'{self.base_url}/geral/clientes/', json=data, headers=headers)
            response.raise_for_status()
            clientes = response.json().get('clientes_cadastro', [])
            fornecedores = [
                cliente for cliente in clientes
                if cliente.get('tags') and any(tag.get('tag') == 'Fornecedor' for tag in cliente.get('tags', []))
            ]
            return fornecedores
        except requests.RequestException as e:
            self.logger.error(f'Erro na requisição Omie: {e}')
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
                # Endpoint correto para categorias
                response = requests.post(f'{self.base_url}/geral/categorias/', json=data, headers=headers)
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
                self.logger.error(f'Erro na requisição Omie: {e}')
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
            # Endpoint correto para incluir clientes
            response = requests.post(f'{self.base_url}/geral/clientes/', json=data, headers=headers)
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
            self.logger.error(f'Erro na requisição Omie: {error_message}')
            return {"error": error_message}

    def criar_conta_pagar(self, payment_request):
        """
        Cria uma conta a pagar no Omie baseada na solicitação de pagamento.
        """
        data = {
            "call": "IncluirContaPagar",
            "app_key": self.omie_app_key,
            "app_secret": self.omie_app_secret,
            "param": [
                {
                    "codigo_lancamento_integracao": payment_request.id,
                    "codigo_cliente_fornecedor": payment_request.supplier,
                    "data_vencimento": payment_request.due_date.strftime('%d/%m/%Y'),
                    "data_entrada": payment_request.service_date.strftime('%d/%m/%Y'),
                    "valor_documento": float(payment_request.amount),
                    "codigo_categoria": payment_request.category,
                    "observacao": f"nº {payment_request.protocol}: {payment_request.description}",
                    "distribuicao": [
                        {
                            "cCodDep": payment_request.department.id_omie,
                            "nPerDep": "100",
                            "nValDep": float(payment_request.amount)
                        }
                    ]
                }
            ]
        }

        headers = {
            'Content-Type': 'application/json'
        }

        try:
            # Endpoint correto para contas a pagar
            response = requests.post(f'{self.base_url}/financas/contapagar/', json=data, headers=headers)
            response.raise_for_status()
            response_data = response.json()

            # Verifique a resposta para erros específicos do Omie
            if response_data.get("codigo_status") != "0":
                error_message = response_data.get("descricao_status", "Erro desconhecido do Omie.")
                return {"error": error_message}

            self.logger.info(f"Conta a pagar criada com sucesso no Omie para solicitação {payment_request.id}.")
            return response_data

        except requests.RequestException as e:
            # Log do erro
            self.logger.error(f'Erro ao criar conta a pagar no Omie: {e}')
            return {"error": str(e)}


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


class ManagerApprovalView(APIView):

    def post(self, request):
        data = request.data
        payment_request_id = data.get('payment_request_id')
        manager_answer = data.get('manager_answer')

        # Validação da resposta do gestor
        if manager_answer not in ["Aprovado", "Reprovado"]:
            return Response(
                {"error": "Resposta do gestor inválida. Deve ser 'Aprovado' ou 'Reprovado'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment_request = PaymentRequest.objects.get(id=payment_request_id)
        except PaymentRequest.DoesNotExist:
            return Response(
                {"error": "Solicitação de pagamento não encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Atualizar o status do gestor e o status de solicitação
        payment_request.manager_status = manager_answer
        payment_request.requesting_status = "Em andamento" if manager_answer == "Aprovado" else "Cancelado"
        payment_request.save()
        logger.info(f"Solicitação de pagamento {payment_request_id} atualizada para status '{manager_answer}'.")

        # Se aprovado, enviar para o Omie
        if manager_answer == "Aprovado":
            omie_service = OmieService()
            omie_response = omie_service.criar_conta_pagar(payment_request)

            if "error" in omie_response:
                logger.error(f"Erro ao enviar para o Omie: {omie_response['error']}")
                return Response(
                    {"error": f"Falha ao enviar para o Omie: {omie_response['error']}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            else:
                logger.info(f"Solicitação de pagamento {payment_request_id} enviada com sucesso para o Omie.")
                payment_request.financial_status = "Enviado para Omie"
                payment_request.id_omie = omie_response.get('codigo_lancamento_omie')
                payment_request.save()

        return Response(
            {"message": "Status do gestor atualizado com sucesso."},
            status=status.HTTP_200_OK
        )


class PaymentPaidWebhookView(APIView):
    """
    View para receber webhooks do Omie quando uma conta a pagar for paga.
    Atualiza o status financeiro e do solicitante na solicitação de pagamento.
    """

    def post(self, request):
        data = request.data
        logger.info(f"Recebido webhook de baixa do Omie: {data}")

        # Verificar se o tópico é o esperado
        topic = data.get('topic', '')
        if topic != "Financas.ContaPagar.BaixaRealizada":
            logger.warning(f"Tópico inesperado: {topic}")
            return Response({"error": "Tópico inválido."}, status=status.HTTP_400_BAD_REQUEST)

        events = data.get('event', [])

        if not events:
            logger.warning("Nenhum evento encontrado no webhook.")
            return Response({"error": "Nenhum evento encontrado."}, status=status.HTTP_400_BAD_REQUEST)

        for event in events:
            contas_a_pagar = event.get('conta_a_pagar', [])

            for conta in contas_a_pagar:
                codigo_lancamento_integracao = conta.get('codigo_lancamento_integracao')
                codigo_lancamento_omie = conta.get('codigo_lancamento_omie')

                if codigo_lancamento_integracao:
                    try:
                        payment_request = PaymentRequest.objects.get(id_omie=codigo_lancamento_integracao)
                    except PaymentRequest.DoesNotExist:
                        logger.error(f"PaymentRequest com código de integração '{codigo_lancamento_integracao}' não encontrado.")
                        continue

                    # Atualizar os status
                    payment_request.financial_status = "Pago"
                    payment_request.requesting_status = "Concluído"
                    payment_request.save()

                    logger.info(f"PaymentRequest '{payment_request.id}' atualizado para 'Pago' e solicitante para 'Concluído'.")

                elif codigo_lancamento_omie:
                    # Caso 'codigo_lancamento_integracao' não esteja disponível, tente mapear pelo 'codigo_lancamento_omie'
                    try:
                        payment_request = PaymentRequest.objects.get(id_omie=codigo_lancamento_omie)
                    except PaymentRequest.DoesNotExist:
                        logger.error(f"PaymentRequest com código de lançamento Omie '{codigo_lancamento_omie}' não encontrado.")
                        continue

                    # Atualizar os status
                    payment_request.financial_status = "Pago"
                    payment_request.requesting_status = "Concluído"
                    payment_request.save()

                    logger.info(f"PaymentRequest '{payment_request.id}' atualizado para 'Pago' e solicitante para 'Concluído'.")
                else:
                    logger.error("Nenhum identificador encontrado na conta a pagar para mapear a solicitação de pagamento.")
                    continue

        return Response({"message": "Webhook processado com sucesso."}, status=status.HTTP_200_OK)