import logging
import os
from datetime import datetime

import requests
import workdays
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q, Sum, Prefetch, Value, Case, When, BooleanField, F, DecimalField
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from weasyprint import HTML
from rest_framework.decorators import action
from accounts.models import User
from api.views import BaseModelViewSet
from core.models import Comment
from .models import *
from .serializers import *
from django.core.cache import cache
from hashlib import md5
from django.db.models.functions import Coalesce


logger = logging.getLogger(__name__)


class FinancierViewSet(BaseModelViewSet):
    queryset = Financier.objects.all()
    serializer_class = FinancierSerializer


class PaymentViewSet(BaseModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        query = Payment.objects.select_related(
            'sale',
            'sale__customer',
            'sale__branch',
        ).prefetch_related(
            'installments',
        )
        
        return query.order_by('-created_at')
            

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
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        sale_status = request.query_params.get('sale_status', None)
        sale_customer = request.query_params.get('sale_customer', None)
        sale_payment_status = request.query_params.get('sale_payment_status', None)
        sale_marketing_campaign = request.query_params.get('sale_marketing_campaign', None)
        sale_branch = request.query_params.get('sale_branch', None)
        principal_final_service_opinion = request.query_params.get('principal_final_service_opinion__in', None)
        final_service_opinions = request.query_params.get('final_service_opinions__in', None)
        
        if principal_final_service_opinion:
            principal_final_service_opinion = principal_final_service_opinion.split(',')
            queryset = queryset.filter(sale__projects__inspection__final_service_opinion__id__in=principal_final_service_opinion)
            
        if final_service_opinions:
            final_service_opinions = final_service_opinions.split(',')
            queryset = queryset.filter(sale__projects__field_services__final_service_opinion__id__in=final_service_opinions)
        
        if sale_branch:
            queryset = queryset.filter(sale__branch__id=sale_branch)
        
        if sale_marketing_campaign:
            queryset = queryset.filter(sale__marketing_campaign__id__in=sale_marketing_campaign)
        
        if sale_payment_status:
            sale_payment_status_list = sale_payment_status.split(',')
            queryset = queryset.filter(sale__payment_status__in=sale_payment_status_list)
        
        if sale_customer:
            queryset = queryset.filter(sale__customer__id=sale_customer)
        
        if sale_status:
            sale_status_list = sale_status.split(',')
            queryset = queryset.filter(sale__status__in=sale_status_list)
            
            
        page = self.paginate_queryset(queryset)
        if page is not None:
            serialized_data = self.get_serializer(page, many=True).data
            return self.get_paginated_response(serialized_data)
        
        serialized_data = self.get_serializer(queryset, many=True).data
        return Response(serialized_data)


    @action(detail=False, methods=['get'])
    def indicators(self, request, *args, **kwargs):
        filter_params = request.GET.dict()
        filter_hash = md5(str(filter_params).encode()).hexdigest()
        cache_key = f'payments_indicators_{filter_hash}'

        combined_indicators = cache.get(cache_key)
        if combined_indicators:
            return Response({"indicators": combined_indicators})

        # Base queryset com os filtros aplicados
        qs = self.filter_queryset(self.get_queryset())

        installments_indicators = qs.aggregate(
            overdue_installments_count=Count(
                'installments',
                filter=Q(installments__is_paid=False, installments__due_date__lte=timezone.now())
            ),
            overdue_installments_value=Coalesce(
                Sum(
                    'installments__installment_value',
                    filter=Q(installments__is_paid=False, installments__due_date__lte=timezone.now()),
                    output_field=DecimalField()
                ),
                Value(0, output_field=DecimalField())
            ),
            on_time_installments_count=Count(
                'installments',
                filter=Q(installments__is_paid=False, installments__due_date__gt=timezone.now())
            ),
            on_time_installments_value=Coalesce(
                Sum(
                    'installments__installment_value',
                    filter=Q(installments__is_paid=False, installments__due_date__gt=timezone.now()),
                    output_field=DecimalField()
                ),
                Value(0, output_field=DecimalField())
            ),
            
            paid_installments_count=Count(
                'installments',
                filter=Q(installments__is_paid=True)
            ),
            paid_installments_value=Coalesce(
                Sum(
                    'installments__installment_value',
                    filter=Q(installments__is_paid=True),
                    output_field=DecimalField()
                ),
                Value(0, output_field=DecimalField())
            ),
            total_installments=Count('installments'),
            total_installments_value=Coalesce(
                Sum(
                    'installments__installment_value',
                    output_field=DecimalField()
                ),
                Value(0, output_field=DecimalField())
            )
        )

        qs_consistency = qs.annotate(
            total_installments_value=Coalesce(
                Sum('installments__installment_value', output_field=DecimalField()),
                Value(0, output_field=DecimalField())
            ),
            total_installments_count=Count('installments'),
            paid_installments_count=Count('installments', filter=Q(installments__is_paid=True))
        ).annotate(
            is_consistent=Case(
                When(
                    Q(total_installments_count=F('paid_installments_count')) &
                    Q(value=F('total_installments_value')),
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        )
        consistency_indicators = qs_consistency.aggregate(
            total_payments=Count('id'),
            total_payments_value=Coalesce(
                Sum('value', output_field=DecimalField()),
                Value(0, output_field=DecimalField())
            ),
            consistent_payments=Count('id', filter=Q(is_consistent=True)),
            consistent_payments_value=Coalesce(
                Sum('value', filter=Q(is_consistent=True), output_field=DecimalField()),
                Value(0, output_field=DecimalField())
            ),
            inconsistent_payments_value=Coalesce(
                Sum('value', filter=~Q(is_consistent=True), output_field=DecimalField()),
                Value(0, output_field=DecimalField())
            ),
            inconsistent_payments=Count('id', filter=~Q(is_consistent=True))
        )

        # Combina os dois conjuntos de indicadores
        combined_indicators = {
            "installments": installments_indicators,
            "consistency": consistency_indicators
        }

        cache.set(cache_key, combined_indicators, 60)
        return Response({"indicators": combined_indicators})


class PaymentInstallmentViewSet(BaseModelViewSet):
    queryset = PaymentInstallment.objects.all()
    serializer_class = PaymentInstallmentSerializer


class FranchiseInstallmentViewSet(BaseModelViewSet):
    queryset = FranchiseInstallment.objects.all()
    serializer_class = FranchiseInstallmentSerializer


class FinancialRecordViewSet(BaseModelViewSet):
    queryset = FinancialRecord.objects.all()
    serializer_class = FinancialRecordSerializer
    
    def get_queryset(self):
        query = super().get_queryset()

        user = self.request.user
        employee = user.employee
        employee_department = employee.department

        # Definindo os conjuntos de departamentos
        DEPT_SET_1_IDS = [6, 2, 17]  # Financeiro, Tecnologia, Contabilidade
        DEPT_SET_2_IDS = [18, 7]  # Pós-Venda, Sucesso do Cliente
        DEPT_SET_3_IDS = [3, 12, 13, 20]  # Vistoria, Financeiro do CO, Obras, Instalação

        # Verificando se o usuário atual está em DEPT_SET_1 ou DEPT_SET_2
        condition_a = user.has_perm('financial.view_all_payable_financial_records')
        condition_b = employee_department.id in DEPT_SET_1_IDS
        condition_c = employee_department.id in DEPT_SET_2_IDS
        condition_d = user.has_perm('financial.view_all_department_payable_financial_records')
        condition_e = employee_department.id == 12  # Financeiro do CO
        
        # print(f"Conditions: {condition_a}, {condition_b}, {condition_c}, {condition_d}, {condition_e}")

        # Todos os usuários podem ver solicitações onde são o responsável ou solicitante
        include_q = Q(responsible=user) | Q(requester=user)

        if condition_a or condition_b:
            if self.request.GET.get('bug') == 'true':
                return query.filter(responsible_status='A', payment_status='P', integration_code__isnull=True)
            # Usuários do DEPT_SET_1 podem ver todas as solicitações sem filtros
            return query  # Retorna todas as solicitações sem aplicar nenhum filtro
        elif condition_e:
            include_q |= Q(requesting_department__in=DEPT_SET_3_IDS)
        elif condition_d:
            # Usuários com a permissão podem ver todos os pagamentos do seu departamento
            include_q |= Q(requesting_department=employee_department)
        elif condition_c:
            # Usuários do DEPT_SET_2 podem ver todas as solicitações desses departamentos
            include_q |= Q(requesting_department__in=DEPT_SET_2_IDS)
        # Caso contrário, include_q permanece como está (responsável ou solicitante)

        # Aplica o filtro ao queryset
        query = query.filter(include_q)

        return query

    def create(self, request, *args, **kwargs):
        
        user = request.user
        employee = user.employee
        
        request.data['requester'] = user.id
        request.data['responsible'] = employee.user_manager.id
                
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.responsible_status != 'P':
            return Response({"error": "A solicitação não está pendente de aprovação."}, status=400)
        
        cancel_url = os.environ.get('CANCEL_FINANCIAL_RECORD_APPROVAL_URL')
        if cancel_url:
            body = {
                "responsible_request_integration_code": instance.responsible_request_integration_code
            }
            cancel_response = requests.post(cancel_url, json=body)
            logger.info(f"Cancel approval request response: {cancel_response.status_code} - {cancel_response.text}")
        else:
            logger.warning("CANCEL_FINANCIAL_RECORD_APPROVAL_URL não está definido nas variáveis de ambiente.")

        OmieIntegrationView().update_payment_request(instance)
        return super().update(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        generate_pdf = request.query_params.get('generate_pdf', 'false').lower() == 'true'
        
        if generate_pdf:
            template_path = 'financial_record_pdf.html'
            context = {'object': instance}

            # Renderiza o template para HTML
            template = get_template(template_path)
            html = template.render(context)

            # Converte o HTML para PDF usando WeasyPrint com suporte a arquivos estáticos
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="solicitacao_{instance.protocol}.pdf"'

            # Usa WeasyPrint para converter HTML em PDF e garantir que as URLs estáticas sejam resolvidas
            HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(response)
            return response
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class OmieIntegrationView(APIView):
    
    OMIE_API_URL = os.environ.get('OMIE_API_URL')
    OMIE_ACESSKEY = os.environ.get('OMIE_ACESSKEY')
    OMIE_ACESSTOKEN = os.environ.get('OMIE_ACESSTOKEN')
    
    def post(self, request):
        if not self.OMIE_API_URL or not self.OMIE_ACESSKEY or not self.OMIE_ACESSTOKEN:
            return Response({"error": "API URL, AcessKey and AccessToken not set in environment variables"}, status=500)
        
        omie_call = request.data.get('call', None)
        
        if omie_call == 'ListarDepartamentos':
            return self.list_departments()
            
        if omie_call == 'ListarCategorias':
            return self.list_categories()
            
        if omie_call == 'ListarClientesResumido':
            filter = request.data.get('filter', None)
            return self.list_customers(filter)
        
        if omie_call == 'IncluirCliente':
            return self.create_customer(request.data.get('customer', None))
        
        return Response({"error": "Invalid call parameter"}, status=400)
    
    def list_departments(self):
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
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            departments = response.json().get('departamentos', [])
            active_departments = [dept for dept in departments if dept.get('inativo') == 'N']
            return Response(active_departments)
        else:
            return Response({"error": "Failed to fetch data from Omie API"}, status=response.status_code)
    
    def list_categories(self):
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
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            categories = response.json().get('categoria_cadastro', [])
            active_categories = [
                cat for cat in categories 
                if cat.get('totalizadora') == 'N'
                and cat.get('conta_inativa') == 'N'
                and cat.get('nao_exibir') == 'N'
                and cat.get('conta_despesa') == 'S'
            ]
            return Response(active_categories)
        else:
            return Response({"error": "Failed to fetch data from Omie API"}, status=response.status_code)
    
    def list_customers(self, filter):
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
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            clients = response.json().get('clientes_cadastro_resumido', [])
            return Response(clients)
        else:
            return Response({"error": "Failed to fetch data from Omie API"}, status=response.status_code)
        
    def create_customer(self, customer):
        url = f"{self.OMIE_API_URL}/geral/clientes/"
        headers = {
            'Content-Type': 'application/json',
        }
        
        cnpj_cpf = customer.get('cnpj_cpf', None)
        name = customer.get('name', None)
        
        data = {
            "call": "IncluirCliente",
            "app_key": self.OMIE_ACESSKEY,
            "app_secret": self.OMIE_ACESSTOKEN,
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

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return Response(response.json())
        else:
            return Response({"error": "Failed to create customer in Omie", "details": response.json()}, status=response.status_code)
        
    def get_supplier(self, codigo_cliente_omie):
        url = f"{self.OMIE_API_URL}/geral/clientes/"
        data = {
            "call": "ConsultarCliente",
            "app_key": os.getenv('OMIE_ACESSKEY'),
            "app_secret": os.getenv('OMIE_ACESSTOKEN'),
            "param": [{"codigo_cliente_omie": codigo_cliente_omie}]
        }
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            if "razao_social" in result and "cnpj_cpf" in result:
                return {"razao_social": result.get("razao_social"), "cnpj_cpf": result.get("cnpj_cpf")}
            else:
                logger.error(f"Fornecedor sem documento ou nome: {result}")
                return Response({"error": "Supplier without document or name"}, status=500)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch supplier from Omie: {e}")
            return Response({"error": "Failed to fetch supplier from Omie", "details": str(e)}, status=500)

    def create_payment_request(self, financial_record, manager_status="Aprovado", manager_note=None):
        if manager_status == "Aprovado":
            url = f"{self.OMIE_API_URL}/financas/contapagar/"
            headers = {
                'Content-Type': 'application/json',
            }
            data = {
                "call": "IncluirContaPagar",
                "app_key": self.OMIE_ACESSKEY,
                "app_secret": self.OMIE_ACESSTOKEN,
                "param": [
                    {
                        "codigo_lancamento_integracao": financial_record.id,
                        "codigo_cliente_fornecedor": financial_record.client_supplier_code,
                        "data_vencimento": financial_record.due_date.strftime('%d/%m/%Y'),
                        "valor_documento": financial_record.value,
                        "codigo_categoria": financial_record.category_code,
                        "data_previsao": financial_record.due_date.strftime('%d/%m/%Y'),
                        "numero_documento_fiscal": financial_record.invoice_number if financial_record.invoice_number else '',
                        "data_emissao": financial_record.service_date.strftime('%d/%m/%Y'),
                        "observacao": f'nº {financial_record.protocol}: {financial_record.notes}',
                        "distribuicao": [
                            {
                                "cCodDep": financial_record.department_code,
                                "nPerDep": "100",
                                "nValDep": financial_record.value
                            }
                        ]
                    }
                ]
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                financial_record.integration_code = response.json().get('codigo_lancamento_omie', None)
                financial_record.save()
            else:
                logger.error(f"Failed to create financial record in Omie: {response.json()}")
        
        financial_record.status = 'E'
        financial_record.responsible_status = 'A' if manager_status == 'Aprovado' else 'R'
        financial_record.responsible_response_date = timezone.now()
        financial_record.responsible_notes = manager_note
        financial_record.save()
        
        if manager_status == "Aprovado":
            return Response(response.json(), status=response.status_code)
        else:
            return Response({"message": "Financial record updated without sending to Omie"}, status=200)
        
    def update_payment_request(self, financial_record):
        url = f"{self.OMIE_API_URL}/financas/contapagar/"
        headers = {
            'Content-Type': 'application/json',
        }
        data = {
            "call": "AlterarContaPagar",
            "app_key": self.OMIE_ACESSKEY,
            "app_secret": self.OMIE_ACESSTOKEN,
            "param": [
                {
                    "codigo_lancamento_integracao": financial_record.id,
                    "codigo_cliente_fornecedor": financial_record.client_supplier_code,
                    "data_vencimento": financial_record.due_date.strftime('%d/%m/%Y'),
                    "valor_documento": financial_record.value,
                    "codigo_categoria": financial_record.category_code,
                    "data_previsao": financial_record.due_date.strftime('%d/%m/%Y'),
                    "numero_documento_fiscal": financial_record.invoice_number if financial_record.invoice_number else '',
                    "data_emissao": financial_record.service_date.strftime('%d/%m/%Y'),
                    "observacao": f'nº {financial_record.protocol}: {financial_record.notes}',
                    "distribuicao": [
                        {
                            "cCodDep": financial_record.department_code,
                            "nPerDep": "100",
                            "nValDep": financial_record.value
                        }
                    ]
                }
            ]
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return Response(response.json(), status=response.status_code)
        else:
            logger.error(f"Failed to update payment request in Omie: {response.json()}")
            return Response({"error": response.json()}, status=response.status_code)


class FinancialRecordApprovalView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):

        action = request.data.get('Action', None)
        rows = request.data.get('Rows', [])
        
        if action != 'Edit' or not rows:
            return Response({"error": "Invalid request format"}, status=400)
        
        for row in rows:
            financial_record_id = row.get('financial_record_id', None)
            manager_status = row.get('manager_status', None)
            manager_note = row.get('manager_note', None)
            
            if not financial_record_id or not manager_status:
                return Response({"error": "Missing financial_record_id or manager_status"}, status=400)
            
            try:
                financial_record = FinancialRecord.objects.get(id=financial_record_id)
            except FinancialRecord.DoesNotExist:
                return Response({"error": f"FinancialRecord with id {financial_record_id} does not exist"}, status=404)
            
            if financial_record.responsible_status != 'P':
                return Response({"error": f"FinancialRecord with id {financial_record_id} is not pending approval"}, status=400)
            
            try:
                # Atualiza a data de vencimento caso a data atual seja menor ou igual a data de hoje
                now = timezone.localtime(timezone.now()).date()
                if financial_record.due_date <= now:
                    financial_record.due_date = workdays.workday(now, 2)
                    financial_record.save()
                    logger.info(f"Due date for financial record {financial_record.protocol} updated to {financial_record.due_date}")
            except Exception as e:
                logger.error(f"Failed to update due date for financial record {financial_record_id}: {e}")
                
            try:
                response = OmieIntegrationView().create_payment_request(financial_record, manager_status, manager_note)
                if response.status_code == 200:
                    financial_record.integration_code = response.data.get('codigo_lancamento_omie', None)
                    
                    financial_record.save()
            except Exception as e:
                logger.error(f"Failed to create payment request in Omie: {e}")
        
        return Response({"message": "Financial record(s) approved"})


class UpdateFinancialRecordPaymentStatus(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        logger.debug(f"Request data: {request.data}")
        
        if request.data == {'ping': 'omie'}:
            logger.debug("Received ping from Omie, responding with pong")
            return Response({"message": "pong"})
        
        event = request.data.get('event', {})
        financial_record_id = None
        
        if isinstance(event, dict):
            financial_record_id = event.get('codigo_lancamento_integracao', None)
        elif isinstance(event, list) and len(event) > 0:
            conta_a_pagar = event[0].get('conta_a_pagar', [])
            if len(conta_a_pagar) > 0:
                financial_record_id = conta_a_pagar[0].get('codigo_lancamento_integracao', None)
        
        topic = request.data.get('topic', None)
        
        if not financial_record_id:
            logger.error("Missing codigo_lancamento_integracao")
            return Response({"error": "Missing financial_record_id"}, status=400)
        
        try:
            financial_record = FinancialRecord.objects.get(id=financial_record_id)
        except FinancialRecord.DoesNotExist:
            return Response({"error": f"FinancialRecord with id {financial_record_id} does not exist"}, status=404)
        
        if topic == 'Financas.ContaPagar.BaixaRealizada':
            financial_record.payment_status = 'PG'
            financial_record.status = 'C'
        elif topic in ['Financas.ContaPagar.Excluido', 'Financas.ContaPagar.BaixaCancelada']:
            financial_record.payment_status = 'C'
            author_email = request.data.get('author', {}).get('email', None)
            if author_email:
                try:
                    author = User.objects.get(email=author_email)
                except User.DoesNotExist:
                    author = None
                    
                Comment.objects.create(
                    author=author,
                    content_type=ContentType.objects.get_for_model(FinancialRecord),
                    object_id=financial_record_id,
                    text=f"A solicitação de pagamento {financial_record.protocol} foi {'cancelada' if 'BaixaCancelada' in topic else 'excluída'} no Omie por {author.complete_name if author else 'Desconhecido'}.",
                    is_system_generated=True
                )
        
        financial_record.paid_at = timezone.now()
        financial_record.save()
        
        return Response({"message": "Financial record payment status updated"})
