from datetime import datetime
import logging
import re

from django.db import transaction
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from weasyprint import HTML

from accounts.models import PhoneNumber, UserType
from accounts.serializers import PhoneNumberSerializer, UserSerializer
from api.views import BaseModelViewSet
from logistics.models import Product, ProductMaterials, SaleProduct
from resolve_crm.clicksign import create_clicksign_document, create_signer, create_document_signer
from .models import *
from .serializers import *
from django.db.models import Count, Q



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
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Indicadores
        indicators = queryset.aggregate(
            pending_count=Count('id', filter=Q(status="P")),
            finalized_count=Count('id', filter=Q(status="F")),
            in_progress_count=Count('id', filter=Q(status="EA")),
            canceled_count=Count('id', filter=Q(status="C")),
            terminated_count=Count('id', filter=Q(status="D")),
        )
        
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


class GenerateContractView(APIView):
    def post(self, request):
        sale_id = request.data.get('sale_id')
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response({'message': 'Venda não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        
        contract_template = ContractTemplate.objects.first() # Hardcoded para o MVP

        # Obter as variáveis para substituição
        variables = request.data.get('contract_data', {})
        if not isinstance(variables, dict):
            return Response({'message': 'As variáveis devem ser um dicionário.'}, status=status.HTTP_400_BAD_REQUEST)

        # Substituir variáveis no conteúdo do template
        contract_content = contract_template.content
        for key, value in variables.items():
            contract_content = re.sub(fr"{{{{\s*{key}\s*}}}}", str(value), contract_content)

        # Gerar o PDF
        try:
            rendered_html = render_to_string('contract_base.html', {'content': contract_content})
            pdf = HTML(string=rendered_html).write_pdf()
        except Exception as e:
            return Response({'message': f'Erro ao gerar o PDF: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        pdf = HTML(string=rendered_html).write_pdf()
        logger.debug("Tamanho do PDF gerado: %d bytes", len(pdf))
        
        # Enviar o PDF para o Clicksign
        try:
            clicksign_response, doc_key = create_clicksign_document(sale.contract_number, sale.customer.complete_name, pdf)
            if clicksign_response.get('status') == 'error':
                raise ValueError(clicksign_response.get('message'))
        except ValueError as ve:
            return Response({'message': f'Erro ao criar o documento no Clicksign: {ve}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'message': f'Erro inesperado ao criar o documento no Clicksign: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            clicksign_response_for_signer = create_signer(sale.customer)
            if clicksign_response_for_signer.get('status') == 'error':
                raise ValueError(clicksign_response_for_signer.get('message'))
        except ValueError as ve:
            return Response({'message': f'Erro ao criar o signatário no Clicksign: {ve}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:  
            return Response({'message': f'Erro inesperado ao criar o signatário no Clicksign: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            signer_key = clicksign_response_for_signer.get('signer_key')
            clicksign_response_for_document_signer = create_document_signer(doc_key, signer_key)
            if clicksign_response_for_document_signer.get('status') == 'error':
                raise ValueError(clicksign_response_for_document_signer.get('message'))
        except ValueError as ve:
            return Response({'message': f'Erro ao criar o signatário do documento no Clicksign: {ve}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Criar o objeto na tabela Attachment
        try:
            now = datetime.now().strftime('%Y%m%d%H%M%S')
            file_name = f"contrato_{sale.contract_number}_{now}.pdf"
            sanitized_file_name = re.sub(r'[^a-zA-Z0-9_.]', '_', file_name)

            attachment = Attachment.objects.create(
                object_id=sale_id,
                content_type_id=ContentType.objects.get_for_model(ContractTemplate).id,
                status="Em Análise",
            )

            attachment.file.save(sanitized_file_name, ContentFile(pdf))
        except Exception as e:
            return Response({'message': f'Erro ao salvar o arquivo: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({'message': f'Contrato gerado com sucesso. Envio ao Clicksign efetuado. {clicksign_response}', 'attachment_id': attachment.id}, status=status.HTTP_200_OK)


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
