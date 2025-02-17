import base64
from datetime import datetime, timezone
from io import BytesIO
import logging
import os
import qrcode
import re

from django.db import transaction
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import formats
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from weasyprint import HTML

from accounts.models import PhoneNumber, UserType
from accounts.serializers import PhoneNumberSerializer, UserSerializer
from api.views import BaseModelViewSet
from logistics.models import Product, ProductMaterials, SaleProduct
from resolve_crm.clicksign import activate_envelope, add_envelope_requirements, create_clicksign_document, create_clicksign_envelope, create_signer, send_notification
from .models import *
from .serializers import *
from django.db.models import Count, Q, Sum
from django.db.models import Exists, OuterRef, Q, Value, Case, When, CharField, Prefetch
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny



logger = logging.getLogger(__name__)


class OriginViewSet(BaseModelViewSet):
    queryset = Origin.objects.all()
    serializer_class = OriginSerializer


class LeadViewSet(BaseModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    filter_fields = '__all__'


class LeadTaskViewSet(BaseModelViewSet): 
    queryset = Task.objects.all()
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

    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser or user.has_perm('resolve_crm.view_all_sales'):
            # Retorna todas as vendas para superusuários e usuários com permissão
            return self.queryset
        
        if user.employee.related_branches:
            # Filtra as vendas onde a filial do usuário é a mesma da venda
            branch_sales = self.queryset.filter(branch__in=user.employee.related_branches.all())
        else:
            branch_sales = self.queryset.none()
        
        # Filtra as vendas onde o usuário é um dos stakeholders
        stakeholder_sales = self.queryset.filter(
            Q(customer=user) | 
            Q(seller=user) | 
            Q(sales_supervisor=user) | 
            Q(sales_manager=user)
        )
        
        return branch_sales | stakeholder_sales
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        payment_status = request.query_params.get('invoice_status')
        is_signed = request.query_params.get('is_signed')
        borrower = request.query_params.get('borrower')
        homologator = request.query_params.get('homologator')
        final_service_opinions = request.query_params.get('final_service_options')
        
        if final_service_opinions:
            final_service_opinion_list = final_service_opinions.split(',')
            queryset = queryset.filter(projects__inspection__final_service_opinion__id__in=final_service_opinion_list)
        
        if borrower:
            queryset = queryset.filter(payments__borrower__id=borrower)
        
        if homologator:
            queryset = queryset.filter(projects__homologator__id=homologator)
        
        if is_signed=='true':
            queryset = queryset.filter(signature_date__isnull=False)
        elif is_signed=='false':
            queryset = queryset.filter(signature_date__isnull=True)
            
        if payment_status:
            payment_status_list = payment_status.split(',')
            queryset = queryset.filter(payments__invoice_status__in=payment_status_list)

        raw_indicators = queryset.aggregate(
            pending_count=Count('id', filter=Q(status="P")),
            pending_total_value=Sum('total_value', filter=Q(status="P")),
            
            finalized_count=Count('id', filter=Q(status="F")),
            finalized_total_value=Sum('total_value', filter=Q(status="F")),
            
            in_progress_count=Count('id', filter=Q(status="EA")),
            in_progress_total_value=Sum('total_value', filter=Q(status="EA")),
            
            canceled_count=Count('id', filter=Q(status="C")),
            canceled_total_value=Sum('total_value', filter=Q(status="C")),
            
            terminated_count=Count('id', filter=Q(status="D")),
            terminated_total_value=Sum('total_value', filter=Q(status="D")),
            
            total_value_sum=Sum('total_value')
        )

        indicators = {
            "pending": {
                "count": raw_indicators["pending_count"],
                "total_value": raw_indicators["pending_total_value"],
            },
            "finalized": {
                "count": raw_indicators["finalized_count"],
                "total_value": raw_indicators["finalized_total_value"],
            },
            "in_progress": {
                "count": raw_indicators["in_progress_count"],
                "total_value": raw_indicators["in_progress_total_value"],
            },
            "canceled": {
                "count": raw_indicators["canceled_count"],
                "total_value": raw_indicators["canceled_total_value"],
            },
            "terminated": {
                "count": raw_indicators["terminated_count"],
                "total_value": raw_indicators["terminated_total_value"],
            },
            
            "total_value_sum": raw_indicators["total_value_sum"]
        }
        
        # Paginação (se habilitada)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serialized_data = self.get_serializer(page, many=True).data
            return self.get_paginated_response({
                'results': serialized_data,
                'indicators': indicators
            })

        serialized_data = self.get_serializer(queryset, many=True).data
        return Response({
            'results': serialized_data,
            'indicators': indicators
        })

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        return Response(self.get_serializer(sale).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        return Response(self.get_serializer(sale).data, status=status.HTTP_200_OK)


class ProjectViewSet(BaseModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        customer = request.query_params.get('customer')
        is_released_to_engineering = request.query_params.get('is_released_to_engineering')
        inspection_status = request.query_params.get('inspection_status')
        signature_date = request.query_params.get('signature_date')
        product_kwp = request.query_params.get('product_kwp')
        access_opnion = request.query_params.get('access_opnion')
        trt_status = request.query_params.get('trt_status')
        
        if access_opnion == 'liberado':
            queryset = queryset.filter(
                Q(attachments__document_type__name__icontains='ART') &
                Q(attachments__document_type__name__icontains='TRT') &
                Q(attachments__status__in=['A']) &
                Q(units__account_number__isnull=False)
            ).distinct()
        elif access_opnion == 'bloqueado':
            queryset = queryset.exclude(
                Q(attachments__document_type__name__icontains='ART', attachments__status='A') &
                Q(units__account_number__isnull=False) |
                Q(attachments__document_type__name__icontains='ART', attachments__status='EA') |
                Q(attachments__document_type__name__icontains='ART', attachments__status='R')
            ).distinct()
            
        if trt_status:
            trt_status = trt_status.split(',')
            queryset = queryset.filter(
                Q(attachments__document_type__name__icontains='ART') &
                Q(attachments__document_type__name__icontains='TRT') &
                Q(attachments__status__in=trt_status)
                )
            
            
        if inspection_status:
            queryset = queryset.filter(inspection__final_service_opinion__id=inspection_status)

        if signature_date:
            date_range = signature_date.split(',')
            if len(date_range) == 2:
                start_date, end_date = date_range
                queryset = queryset.filter(sale__signature_date__range=[start_date, end_date])
            else:
                queryset = queryset.filter(sale__signature_date=signature_date)

        if product_kwp:
            try:
                product_kwp_value = float(product_kwp)
                lower_bound = product_kwp_value - 2.5
                upper_bound = product_kwp_value + 2.5
                queryset = queryset.filter(product__params__gte=lower_bound, product__params__lte=upper_bound)
            except ValueError:
                return Response({'message': 'Valor inválido para KWP.'}, status=status.HTTP_400_BAD_REQUEST)

        if is_released_to_engineering == 'true':
            queryset = queryset.filter(Q(
                # is_documentation_completed=True,
                sale__status__in=['F'],
                sale__payment_status__in=['L', 'C', 'CO'],
                inspection__final_service_opinion__name__icontains='aprovado',
            ) & ~Q(status__in=['CO'])
            )
        elif is_released_to_engineering == 'false':
            queryset = queryset.filter(
                # Q(is_documentation_completed=False) |
                ~Q(sale__status__in=['F', 'CO']) |
                Q(sale__payment_status__in=['P', 'CA']) |
                ~Q(inspection__final_service_opinion__name__icontains='aprovado')
            )
    
        if customer:
            queryset = queryset.filter(sale__customer__id=customer)

        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serialized_data = self.get_serializer(page, many=True).data
            return self.get_paginated_response({'results': serialized_data})

        serialized_data = self.get_serializer(queryset, many=True).data
        return Response({'results': serialized_data})

    @action(detail=False, methods=['get'])
    def indicators(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        raw_indicators = queryset.aggregate(
            designer_pending_count=Count('id', filter=Q(designer_status="P")),
            designer_in_progress_count=Count('id', filter=Q(designer_status="EA")),
            designer_complete_count=Count('id', filter=Q(designer_status="CO")),
            designer_canceled_count=Count('id', filter=Q(designer_status="C")),
            designer_termination_count=Count('id', filter=Q(designer_status="D")),

            pending_count=Count('id', filter=Q(status="P")),
            in_progress_count=Count('id', filter=Q(status="EA")),
            complete_count=Count('id', filter=Q(status="CO")),
            canceled_count=Count('id', filter=Q(status="C")),
            termination_count=Count('id', filter=Q(status="D")),

            is_released_to_engineering_count=Count(
                'id',
                filter=Q(
                    # Q(is_documentation_completed=True) &
                    Q(sale__status='F') &
                    Q(sale__payment_status__in=['L', 'C', 'CO']) & 
                    Q(inspection__final_service_opinion__name__icontains='aprovado') &
                    ~Q(status__in=['CO']) &
                    Q(sale__is_pre_sale=False)
                )
            ),

            pending_material_list=Count(
                'id',
                filter=Q(
                    # Verifica se o projeto está liberado para engenharia
                    Q(
                        # Q(is_documentation_completed=True) &
                        Q(sale__status='F') &
                        Q(sale__payment_status__in=['L', 'C']) &
                        Q(inspection__final_service_opinion__name__icontains='aprovado') &
                        Q(sale__is_pre_sale=False)
                    ) & Q(material_list_is_completed=False)
                )
            ),

            blocked_to_engineering=Count(
                'id',
                filter=Q(
                    # Q(is_documentation_completed=False) |
                    Q(sale__payment_status__in=['P', 'CA']) |
                    ~Q (sale__status='F') |
                    ~Q(inspection__final_service_opinion__name__icontains='aprovado') |
                    Q(sale__is_pre_sale=True)
                )
            )
        )


        indicators = {
            "designer": {
                "pending": raw_indicators["designer_pending_count"],
                "in_progress": raw_indicators["designer_in_progress_count"],
                "complete": raw_indicators["designer_complete_count"],
                "canceled": raw_indicators["designer_canceled_count"],
                "termination": raw_indicators["designer_termination_count"],
            },
            "general": {
                "pending": raw_indicators["pending_count"],
                "in_progress": raw_indicators["in_progress_count"],
                "complete": raw_indicators["complete_count"],
                "canceled": raw_indicators["canceled_count"],
                "termination": raw_indicators["termination_count"],
            },
            "is_released_to_engineering": raw_indicators["is_released_to_engineering_count"],
            "pending_material_list": raw_indicators["pending_material_list"],
            "blocked_to_engineering": raw_indicators["blocked_to_engineering"],
        }

        return Response({"indicators": indicators})
        
        
class ContractSubmissionViewSet(BaseModelViewSet):
    queryset = ContractSubmission.objects.all()
    serializer_class = ContractSubmissionSerializer


class GenerateSalesProjectsView(APIView):
    http_method_names = ['post', 'get']

    @transaction.atomic
    def post(self, request):
        sale_id = request.data.get('sale_id')

        # Verificar se a venda existe
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response({'message': 'Venda não encontrada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Recuperar os produtos da venda
        sale_products = SaleProduct.objects.filter(sale=sale)
        
        if not sale_products.exists():
            return Response({'message': 'Venda não possui produtos associados.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Projetos já criados para esta venda
        projects = Project.objects.filter(sale=sale)
        
        # Listas para rastrear os resultados
        created_projects = []
        already_existing_projects = []
        
        # Criar um projeto para cada produto da venda, se ainda não existir
        for sale_product in sale_products:
            if projects.filter(product=sale_product.product).exists():
                already_existing_projects.append({
                    'product_id': sale_product.product.id,
                    'product_name': sale_product.product.name,
                })
                continue  # Pula para o próximo produto

            # Dados do projeto
            project_data = {
                'sale_id': sale.id,
                'status': 'P',
                'product_id': sale_product.product.id,
            }
            # Serializar e salvar
            project_serializer = ProjectSerializer(data=project_data)
            if project_serializer.is_valid():
                project = project_serializer.save()
                created_projects.append({
                    'product_id': sale_product.product.id,
                    'product_name': sale_product.product.name,
                })
            else:
                return Response(project_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Verificar o resultado
        if not created_projects:
            return Response({'message': 'Todos os projetos já foram criados.', 'already_existing_projects': already_existing_projects}, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'Projetos gerados com sucesso.',
            'created_projects': created_projects,
            'already_existing_projects': already_existing_projects,
        }, status=status.HTTP_200_OK)


    def get(self, request):
        sale_id = request.query_params.get('sale_id')
        
        if not sale_id:
            return Response({'message': 'É necessário informar o ID da venda.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response({'message': 'Venda não encontrada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Recuperar os produtos e os projetos associados à venda
        sale_products = SaleProduct.objects.filter(sale=sale)
        projects = Project.objects.filter(sale=sale)
        
        already_generated = []
        pending_generation = []
        
        # Verificar quais produtos já possuem projetos e quais estão pendentes
        for sale_product in sale_products:
            if projects.filter(product=sale_product.product).exists():
                already_generated.append({
                    'product_id': sale_product.product.id,
                    'product_name': sale_product.product.name,
                    'amount': sale_product.amount,
                    'value': sale_product.value,
                    'reference_value': sale_product.reference_value,
                    'cost_value': sale_product.cost_value,
                })
            else:
                pending_generation.append({
                    'product_id': sale_product.product.id,
                    'product_name': sale_product.product.name,
                })
        
        response_data = {
            'sale_id': sale.id,
            'sale_status': sale.status,
            'already_generated': already_generated,
            'pending_generation': pending_generation,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class GeneratePreSaleView(APIView): 
    http_method_names = ['post']

    @transaction.atomic
    def post(self, request):
        lead_id = request.data.get('lead_id')
        products = request.data.get('products')
        commercial_proposal_id = request.data.get('commercial_proposal_id')
        # payment_data = request.data.get('payment')

        if not lead_id:
            return Response({'message': 'lead_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not products and not commercial_proposal_id:
            return Response({'message': 'É obrigatório possuir um produto ou uma Proposta Comercial.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if commercial_proposal_id and products:
            return Response({'message': 'commercial_proposal_id e products são mutuamente exclusivos.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if commercial_proposal_id:
            try:
                comercial_proposal = ComercialProposal.objects.get(id=commercial_proposal_id)
            except ComercialProposal.DoesNotExist:
                return Response({'message': 'Proposta Comercial não encontrada.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lead = Lead.objects.get(id=lead_id)
        except Lead.DoesNotExist:
            return Response({'message': 'Lead não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not lead.first_document:
            return Response({'message': 'Lead não possui CPF cadastrado.'}, status=status.HTTP_400_BAD_REQUEST)
        
        phone_number = lead.phone
        match = re.match(r'(\d{2})(\d+)', phone_number)
        if match:
            area_code, number = match.groups()
            phone_data = {
                'country_code': 55,
                'area_code': area_code,
                'phone_number': number,
                'is_main': True,
            }
            phone_serializer = PhoneNumberSerializer(data=phone_data)
            if phone_serializer.is_valid():
                phone = phone_serializer.save()
            else:
                return Response(phone_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
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
                'phone_numbers_ids': [phone.id],
            }
            user_serializer = UserSerializer(data=user_data)
            if user_serializer.is_valid():
                customer = user_serializer.save()
            else:
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Atualiza o cliente existente com os dados do lead, se necessário
            phone_ids = []
            for phone in PhoneNumber.objects.filter(user=customer):
                phone_ids.append(phone.id)
                
            if phone.id not in phone_ids:
                phone_ids.append(phone.id)
            
            user_serializer = UserSerializer(customer, data={
                'complete_name': lead.name,
                'email': lead.contact_email,
                'addresses': [address.id for address in lead.addresses.all()],
                'user_types': UserType.objects.get(id=2).id,
                'phone_numbers_ids': phone_ids,
            }, partial=True)
            if user_serializer.is_valid():
                customer = user_serializer.save()
            else:
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        lead.customer = customer
        lead.save()

        products_ = []
        total_value = comercial_proposal.value if commercial_proposal_id else 0
        if products:
            for product in products:
                # Verificar se é um novo produto ou um existente
                if 'id' not in product:
                    # Criar novo produto
                    product_serializer = ProductSerializer(data=product)
                    if product_serializer.is_valid():
                        new_product = product_serializer.save()
                        products_.append(new_product)
    
                        # Calcular o valor do produto com base nos materiais associados
                        product_value = self.calculate_product_value(new_product)
                        total_value += product_value
                    else:
                        return Response(product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Capturar produto existente
                    try:
                        existing_product = Product.objects.get(id=product['id'])
                        products_.append(existing_product)

                        # Calcular o valor do produto com base nos materiais associados
                        product_value = self.calculate_product_value(existing_product)
                        total_value += product_value
                    except Product.DoesNotExist:
                        return Response({'message': f'Produto com id {product["id"]} não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            # Criação da pré-venda usando Serializer
            try:
                seller_id = lead.seller.id
                sales_supervisor_id = lead.seller.employee.user_manager.id if lead.seller.employee.user_manager else None
                sales_manager_id = lead.seller.employee.user_manager.employee.user_manager.id if lead.seller.employee.user_manager and lead.seller.employee.user_manager.employee.user_manager else None
            except Exception as e:
                logger.error(f'Erro ao recuperar informações do vendedor: {str(e)}')
                return Response({'message': 'Erro ao recuperar informações do vendedor.'}, status=status.HTTP_400_BAD_REQUEST)
                
            sale_data = {
                'customer_id': customer.id,
                'lead_id': lead.id,
                'is_pre_sale': True,
                'status': 'P',
                'branch_id': lead.seller.employee.branch.id,
                'seller_id': seller_id,
                'sales_supervisor_id': sales_supervisor_id,
                'sales_manager_id': sales_manager_id,
                'total_value': round(total_value, 3),
                # **({'commercial_proposal_id': commercial_proposal_id} if commercial_proposal_id else {}),
                **({'products_ids': [product.id for product in products_]} if products else {})
            }
            sale_serializer = SaleSerializer(data=sale_data)
            if sale_serializer.is_valid():
                pre_sale = sale_serializer.save()
                
                if commercial_proposal_id:
                    try:
                        salesproduct = SaleProduct.objects.filter(commercial_proposal=comercial_proposal)
                        
                        for saleproduct in salesproduct:
                            if saleproduct.sale:
                                return Response({'message': 'Proposta Comercial já vinculada à uma pré-venda.'}, status=status.HTTP_400_BAD_REQUEST)
                            
                            try:
                                comercial_proposal.status = 'A'
                                comercial_proposal.save()
                                saleproduct.sale = pre_sale
                                saleproduct.save()
                            except Exception as e:
                                logger.error(f'Erro ao vincular produtos da proposta comercial à pré-venda: {str(e)}')
                                return Response({'message': 'Erro ao vincular produtos da proposta comercial à pré-venda.', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                            
                            project_data = {
                                'sale_id': pre_sale.id,
                                'status': 'P',
                                'product_id': saleproduct.product.id,
                                'addresses_ids': [address.id for address in lead.addresses.all()]
                            }
                            project_serializer = ProjectSerializer(data=project_data)
                            if project_serializer.is_valid():
                                project_serializer.save()
                            else:
                                return Response(project_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                            
                    except Exception as e:
                        logger.error(f'Erro ao vincular produtos da proposta comercial à pré-venda: {str(e)}')
                        return Response({'message': 'Erro ao vincular produtos da proposta comercial à pré-venda.', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            else:
                return Response(sale_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Erro ao criar pré-venda: {str(e)}')
            return Response({'message': 'Erro ao criar pré-venda.', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if products:
            # Vinculação dos products ao projeto usando Serializer
            for product in products_:
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
    
    
    def calculate_product_value(self, product):
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


class ContractTemplateViewSet(BaseModelViewSet):
    queryset = ContractTemplate.objects.all()
    serializer_class = ContractTemplateSerializer
    
    
class ValidateContractView(APIView):
    http_method_names = ['get']
    permission_classes = [AllowAny]
    
    def get(self, request):
        envelope_id = request.query_params.get('envelope_id')
        
        if not envelope_id:
            return Response({'message': 'envelope_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        
        contract_submission = ContractSubmission.objects.filter(envelope_id=envelope_id).first()
        if contract_submission is None:
            return Response({'message': 'Contrato não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
        customer_name = contract_submission.sale.customer.complete_name
        masked_email = re.sub(r'(?<=.{2}).(?=.*@)', '*', contract_submission.sale.customer.email)
        masked_phone = re.sub(r'(?<=.{2}).(?=.{2})', '*', contract_submission.sale.customer.phone_numbers.first().phone_number)
        masked_first_document = re.sub(r'(?<=.{3}).', '*', contract_submission.sale.customer.first_document)
        
        return Response({
            'message': f'Contrato validado com sucesso. Cliente: {customer_name}',
            'contract_submission': {
                'sale': {
                    'customer': {
                        'complete_name': customer_name,
                        'email': masked_email,
                        'phone_number': masked_phone,
                        'first_document': masked_first_document,
                    },
                    'seller': {
                        "complete_name": contract_submission.sale.seller.complete_name
                    }
                },
                'status': contract_submission.status,
                'submit_datetime': contract_submission.submit_datetime,
                'due_date': contract_submission.due_date,
            }
        }, status=status.HTTP_200_OK)


class GenerateContractView(APIView):
    http_method_names = ['post']

    @transaction.atomic
    def post(self, request):
        sale_id = request.data.get('sale_id')
        qr_code = ""
        validation_url = ""

        sale = self._get_sale(sale_id)
        if isinstance(sale, Response):
            return sale

        # Valida se campos obrigatórios estão preenchidos
        missing_fields_response = self._validate_sale_data(sale)
        if missing_fields_response:
            return missing_fields_response

        if not sale.payments.exists():
            return Response({'message': 'Venda não possui pagamentos associados.'}, status=status.HTTP_400_BAD_REQUEST)

        total_payments_value = sum(payment.value for payment in sale.payments.all())
        if total_payments_value != sale.total_value:
            return Response({'message': 'A soma dos valores dos pagamentos é diferente do valor total da venda.'}, status=status.HTTP_400_BAD_REQUEST)

        total_payments_value_formatted = formats.number_format(total_payments_value, 2)
        
        variables = self._validate_variables(request.data.get('contract_data', {}))
        if isinstance(variables, Response):
            return variables

        contract_template = ContractTemplate.objects.first()
        if not contract_template:
            return Response({'message': 'Template de contrato não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        customer_data = self._get_customer_data(sale.customer)
        if isinstance(customer_data, Response):
            return customer_data

        preview = request.query_params.get('preview') == 'true'

        if not preview:
            envelope_response = self._create_envelope(sale)
            if isinstance(envelope_response, Response):
                return envelope_response
            
            envelope_id = envelope_response.get('envelope_id')
            if not envelope_id:
                return Response({'message': 'Falha ao obter envelope_id.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            qr_code, validation_url = self._generate_validation_qr_code(envelope_id)

        materials_list = self._generate_materials_list(sale)
        payments_list = self._generate_payments_list(sale)
        projects_data = self._get_projects_data(sale)
        contract_content = self._replace_variables(
            contract_template.content,
            variables,
            customer_data,
            sale.branch.energy_company.name,
            materials_list,
            total_payments_value_formatted,
            payments_list,
            projects_data,
            sale.branch.address.city,
            qr_code=qr_code,
            validation_url=validation_url
        )

        pdf = self._generate_pdf(contract_content)
        if isinstance(pdf, Response):
            return pdf

        if request.query_params.get('preview') == 'true':
            return self._preview_pdf(pdf)

        document_response = self._add_document_to_envelope(sale, envelope_id, pdf)
        if isinstance(document_response, Response):
            return document_response
        document_key = document_response.get('document_key')

        signer_response = self._create_signer(envelope_id, sale.customer)
        if isinstance(signer_response, Response):
            return signer_response
        signer_key = signer_response.get('signer_key')

        add_reqs_response = self._add_envelope_requirements(envelope_id, document_key, signer_key)
        if isinstance(add_reqs_response, Response):
            return add_reqs_response

        activate_response = self._activate_envelope(envelope_id)
        if isinstance(activate_response, Response):
            return activate_response

        notification_response = self._send_notifications(envelope_id)
        if isinstance(notification_response, Response):
            return notification_response

        submission = self._create_contract_submission(sale, document_key, signer_key, envelope_id)
        if isinstance(submission, Response):
            return submission

        return Response({
            'message': 'Contrato gerado com sucesso.',
            'contract_submission_id': submission.id
        }, status=status.HTTP_200_OK)

    def _validate_sale_data(self, sale):
        """
        Verifica campos obrigatórios da venda e do cliente.
        Retorna um Response(400) se algo estiver ausente, senão retorna None.
        """
        missing = []

        if not sale.branch or not sale.branch.energy_company:
            missing.append('Empresa de energia (branch)')

        if not sale.customer:
            missing.append('Dados do cliente')
        else:
            if not sale.customer.complete_name:
                missing.append('Nome do cliente')
            if not sale.customer.first_document:
                missing.append('Documento (CPF/CNPJ) do cliente')

        if missing:
            return Response(
                {'message': f'Campos obrigatórios ausentes: {", ".join(missing)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return None

    def _get_sale(self, sale_id):
        try:
            return Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response({'message': 'Venda não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    def _validate_variables(self, variables):
        if not isinstance(variables, dict):
            return Response({'message': 'As variáveis devem ser um dicionário.'}, status=status.HTTP_400_BAD_REQUEST)
        return variables

    def _get_customer_data(self, customer):
        address = customer.addresses.first()
        if not address:
            return Response({'message': 'Endereço do cliente não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        return {
            'customer_name': customer.complete_name,
            'customer_first_document': customer.first_document,
            'customer_second_document': customer.second_document,
            'customer_street': address.street,
            'customer_house_number': address.number,
            'customer_neighborhood': address.neighborhood,
            'customer_city': address.city,
            'customer_state': address.state,
            'customer_zip_code': address.zip_code,
            'customer_country': address.country,
            'customer_complement': address.complement,
        }

    def _get_projects_data(self, sale):
        projects = sale.projects.all()
        watt_peaks = [f"{project.product.params} kWp" for project in projects]
        if len(watt_peaks) > 1:
            watt_peak = ', '.join(watt_peaks[:-1]) + ' e ' + watt_peaks[-1]
        elif watt_peaks:
            watt_peak = watt_peaks[0]
        else:
            watt_peak = ''
        projects_data = {
            'project_count': len(projects),
            'project_plural': "s" if len(projects) > 1 else "",
            'watt_peak': watt_peak
        }
        return projects_data

    def _generate_materials_list(self, sale):
        materials = []
        for project in sale.projects.all():
            for pm in project.product.materials.filter(is_deleted=False):
                materials.append({
                    'name': pm.material.name,
                    'amount': round(pm.amount, 2),
                    'price': pm.material.price
                })
        materials_html = "".join(f"<li>{m['name']} - Quantidade: {m['amount']:.2f}</li>" for m in materials)
        return materials_html

    def _generate_payments_list(self, sale):
        payments = [
            {
                'type': payment.get_payment_type_display(),
                'value': f"{payment.value:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                'financier': f" - Financiadora: {payment.financier}" if payment.financier else ""
            }
            for payment in sale.payments.all()
        ]
        payments_html = "".join(f"<li>Tipo: {p['type']}{p['financier']} - Valor: R$ {p['value']}</li>" for p in payments)
        return payments_html

    def _replace_variables(self, content, variables, customer_data, energy_company, materials_list, total_value, payments_list, projects_data, city, qr_code, validation_url):
        now = datetime.datetime.now()
        day = now.day
        month = formats.date_format(now, 'F')
        year = now.year
        today_formatted = f'{day} de {month} de {year}'

        variables.update({
            'materials_list': materials_list,
            'payments_list': payments_list,
            'energy_company': energy_company,
            **projects_data,
            **customer_data,
            'today': today_formatted,
            'city': city,
            'total_value': total_value,
            'qr_code': qr_code,
            'validation_url': validation_url
        })
        for key, value in variables.items():
            content = re.sub(fr"{{{{\s*{key}\s*}}}}", str(value), content)
        return content

    def _generate_pdf(self, content):
        try:
            rendered_html = render_to_string('contract_base.html', {'content': content})
            return HTML(string=rendered_html).write_pdf()
        except Exception as e:
            logger.error(f'Erro ao gerar o PDF: {e}')
            return Response({'message': f'Erro ao gerar o PDF: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _preview_pdf(self, pdf):
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="preview_contract.pdf"'
        return response

    def _create_envelope(self, sale):
        try:
            response = create_clicksign_envelope(sale.contract_number, sale.customer.complete_name)
            if response.get('status') == 'success':
                envelope_id = response.get('envelope_id')
                logger.info(f"Envelope criado com ID: {envelope_id}")
                return {'envelope_id': envelope_id}
            else:
                logger.error(f"Erro ao criar envelope: {response.get('message')}")
                return Response({'message': response.get('message')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Erro ao criar envelope: {e}")
            return Response({'message': f'Erro ao criar envelope: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def _generate_validation_qr_code(self, envelope_id):
        validation_url = f"{os.getenv('FRONTEND_URL')}/auth/contract-validation/?envelope_id={envelope_id}"
        qr = qrcode.make(validation_url)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{qr_base64}", validation_url      

    def _add_document_to_envelope(self, sale, envelope_id, pdf):
        try:
            response = create_clicksign_document(envelope_id, sale.contract_number, sale.customer.complete_name, pdf)
            if isinstance(response, dict) and 'data' in response:
                document_data = response['data']
                document_key = document_data['id']
                logger.info(f"Document data: {document_data}")
                if not document_key:
                    logger.error("Chave do documento ausente no retorno do Clicksign.")
                    return Response({'message': 'Chave do documento ausente no retorno do Clicksign.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                logger.info(f"Documento adicionado com chave: {document_key}")
                return {'document_key': document_key}
            elif isinstance(response, dict) and response.get("status") == "error":
                logger.error(f"Erro ao adicionar documento: {response.get('message')}")
                return Response({'message': response.get('message')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.error("Formato inesperado na resposta de `create_clicksign_document`.")
                return Response({'message': 'Formato inesperado na resposta de `create_clicksign_document`.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Erro ao adicionar documento ao envelope: {e}")
            return Response({'message': f'Erro ao adicionar documento ao envelope: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_signer(self, envelope_id, customer):
        try:
            response = create_signer(envelope_id, customer)
            if response.get('status') == 'success':
                signer_key = response.get('signer_key')
                logger.info(f"Signer criado com chave: {signer_key}")
                return {'signer_key': signer_key}
            else:
                logger.error(f"Erro ao criar signer: {response.get('message')}")
                return Response({'message': response.get('message')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Erro ao criar signer: {e}")
            return Response({'message': f'Erro ao criar signer: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def _add_envelope_requirements(self, envelope_id, document_key, signer_key):
        try:
            response = add_envelope_requirements(envelope_id, document_key, signer_key)
            if isinstance(response, list):
                for item in response:
                    if item.get('status') != 'success':
                        logger.error(f"Erro ao adicionar requisitos ao envelope: {item.get('message')}")
                        return Response({'message': item.get('message')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                logger.info("Requisitos do envelope adicionados com sucesso.")
                return {'status': 'success'}
            else:
                logger.error(f"Formato inesperado na resposta de `add_envelope_requirements`: {response}")
                return Response({'message': f'Formato inesperado na resposta de `add_envelope_requirements`: {response}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Erro ao adicionar requisitos ao envelope: {e}")
            return Response({'message': f'Erro ao adicionar requisitos ao envelope: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _activate_envelope(self, envelope_id):
        try:
            response = activate_envelope(envelope_id)
            if response.get('status') == 'success':
                logger.info("Envelope ativado com sucesso.")
                return {'status': 'success'}
            else:
                logger.error(f"Erro ao ativar envelope: {response.get('message')}")
                return Response({'message': response.get('message')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Erro ao ativar envelope: {e}")
            return Response({'message': f'Erro ao ativar envelope: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _send_notifications(self, envelope_id):
        try:
            response = send_notification(envelope_id)
            if response.get('status') == 'success':
                logger.info("Notificações enviadas com sucesso.")
                return {'status': 'success'}
            else:
                logger.error(f"Erro ao enviar notificações: {response.get('message')}")
                return Response({'message': response.get('message')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Erro ao enviar notificações: {e}")
            return Response({'message': f'Erro ao enviar notificações: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_contract_submission(self, sale, document_key, signer_key, envelope_id):
        try:
            submission = ContractSubmission.objects.create(
                sale=sale,
                request_signature_key=signer_key,
                key_number=document_key,
                envelope_id=envelope_id,
                status="P",
                submit_datetime=datetime.datetime.now(tz=timezone.utc),
                due_date=datetime.datetime.now(tz=timezone.utc) + timedelta(days=7),
                link=f"https://app.clicksign.com/envelopes/{envelope_id}"
            )
            logger.info(f"ContractSubmission criado com ID: {submission.id}")
            return submission
        except Exception as e:
            logger.error(f"Erro ao criar ContractSubmission: {e}")
            return Response({'message': f'Erro ao criar ContractSubmission: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerateCustomContract(APIView):
    def post(self, request):
        sale_id = request.data.get('sale_id')
        contract_html = request.data.get('contract_html')

        if not sale_id:
            return Response({'message': 'sale_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not contract_html:
            return Response({'message': 'contract_html é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response({'message': 'Venda não encontrada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Gerando o PDF a partir do HTML
        try:
            rendered_html = render_to_string('contract_base.html', {'content': contract_html})
            pdf = HTML(string=rendered_html).write_pdf()
        except Exception as e:
            return Response({'message': f'Erro ao gerar o PDF: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Salvando o arquivo PDF no backend de armazenamento padrão
        try:
            # Sanitizar o nome do arquivo
            file_name = f"contract_sale_{sale_id}.pdf"
            sanitized_file_name = re.sub(r'[^a-zA-Z0-9_.]', '_', file_name)
            
            # Criar o arquivo no Google Cloud Storage
            attachment = Attachment.objects.create(
                object_id=sale.id,
                content_type_id=ContentType.objects.get_for_model(Sale).id,
                status="Em Análise",
            )
            
            # Salvar o arquivo diretamente no campo `file` do modelo
            attachment.file.save(sanitized_file_name, ContentFile(pdf))

        except Exception as e:
            return Response({'message': f'Erro ao salvar o arquivo: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({'message': 'Contrato gerado com sucesso. Envio ao Clicksign efetuado.', 'attachment_id': attachment.id}, status=status.HTTP_200_OK)
