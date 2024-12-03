import logging
from rest_framework.response import Response
from rest_framework import status
from accounts.models import PhoneNumber, UserType
from accounts.serializers import PhoneNumberSerializer, UserSerializer
from api.views import BaseModelViewSet
from rest_framework.views import APIView
from django.db import transaction

from logistics.models import ProductMaterials
from .serializers import *
from .models import *
from decimal import Decimal
from logistics.models import Product, SaleProduct
from financial.models import FranchiseInstallment
import re



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

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # Extraindo os dados do request
        data = request.data
        print("Request data:", data)
        commercial_proposal_id = data.get('commercial_proposal_id', None)
        print("Commercial proposal ID:", commercial_proposal_id)

        # Inicializando o serializer com os dados recebidos
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        print("Serializer valid data:", serializer.validated_data)

        # Salvando a instância da venda
        sale = serializer.save()
        print("Sale instance created:", sale)
        products_list = []
        total_installment_value = 0

        # Se há uma proposta comercial associada, reutilizar os produtos dela
        if commercial_proposal_id:
            try:
                commercial_proposal = ComercialProposal.objects.get(id=commercial_proposal_id)
                print("Commercial proposal found:", commercial_proposal)
                sale_products = SaleProduct.objects.filter(commercial_proposal=commercial_proposal)
                print("Sale products found:", sale_products)

                if not sale_products.exists():
                    print("No products associated with the commercial proposal.")
                    return Response(
                        {"detail": "Proposta comercial não possui produtos associados."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Verificando se algum produto já está vinculado a uma venda
                if sale_products.filter(sale__isnull=False).exists():
                    print("Commercial proposal already linked to a sale.")
                    return Response(
                        {"detail": "Proposta comercial já vinculada a uma venda."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Associando os produtos da proposta à venda
                for sale_product in sale_products:
                    products_list.append(sale_product)

                    sale_product.sale = sale
                    sale_product.save()
                    print("Sale product linked to sale:", sale_product)

            except ComercialProposal.DoesNotExist:
                print("Commercial proposal not found.")
                return Response(
                    {"detail": "Proposta comercial não encontrada."},
                    status=status.HTTP_404_NOT_FOUND
                )

        else:
            # Caso contrário, associar os produtos enviados diretamente
            products_ids = data.get('products_ids', [])
            print("Products IDs:", products_ids)
            for product_id in products_ids:
                try:
                    product = Product.objects.get(id=product_id)
                    sale_product = SaleProduct.objects.create(
                        sale=sale,
                        product=product,
                        amount=1,  # Ajuste de acordo com sua necessidade
                        value=product.product_value,
                        reference_value=product.reference_value,
                        cost_value=product.cost_value
                    )
                    products_list.append(sale_product)
                    print("Product linked to sale:", product)
                except Product.DoesNotExist:
                    print(f"Product with ID {product_id} not found.")
                    return Response(
                        {"detail": f"Produto com ID {product_id} não encontrado."},
                        status=status.HTTP_404_NOT_FOUND
                    )

        if sale.total_value is None or sale.total_value == 0:
            try:
                total_value = self.calculate_total_value(products_list)
                sale.total_value = total_value
                sale.save()
            except Exception as e:
                print(f"Error calculating total value: {str(e)}")
                return Response(
                    {"detail": "Erro ao calcular o valor total da venda.", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        if sale.sale_products.exists():
            print("Sale products linked to sale:", sale.sale_products.all())
            try:
                total_installment_value = self.calculate_total_installment_value(sale, sale.sale_products.all())
                print("Total installment value:", total_installment_value)
            except Exception as e:
                print(f"Error calculating total installment value: {str(e)}")
                return Response(
                    {"detail": "Erro ao calcular o valor total da parcela.", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        try:
            total_value = sale.total_value
            if total_value:
                franchise_installment = FranchiseInstallment.objects.create(
                    sale=sale,
                    installment_value=total_installment_value,
                )
                print("FranchiseInstallment created:", franchise_installment)
        except Exception as e:
            print(f"Error creating FranchiseInstallment: {str(e)}")
            return Response(
                {"detail": "Erro ao criar a parcela do franqueado.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


        # Retornando a resposta com os dados da nova venda criada
        headers = self.get_success_headers(serializer.data)
        print("Response headers:", headers)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)      
        
    def validate_products_ids(self, products_ids):
        """Valida os IDs dos produtos enviados."""
        products = []
        for product_id in products_ids:
            try:
                product = Product.objects.get(id=product_id)
                products.append(product)
            except Product.DoesNotExist:
                raise ValidationError(
                    {"detail": f"Produto com ID {product_id} não encontrado."}
                )
        return products

    def calculate_linked_products(self, sale, products):
        """Verifica se há projetos vinculados aos produtos."""
        existing_projects = Project.objects.filter(sale=sale, product__in=products).values_list('product_id', flat=True)
        linked_products = [product for product in products if product.id in existing_projects]
        return linked_products

    def remove_unlinked_products(self, sale, products_ids):
        """Remove produtos da venda que não estão mais na lista enviada."""
        existing_sale_products = SaleProduct.objects.filter(sale=sale)
        for sale_product in existing_sale_products:
            if sale_product.product.id not in products_ids:
                sale_product.delete()

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        print("Update request data:", request.data)
        instance = self.get_object()
        data = request.data

        # Atualizando os dados da venda
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()

        # Atualizando os produtos vinculados à venda
        products_ids = data.get('products_ids', [])
        if products_ids:
            try:
                # Validando os produtos
                products = self.validate_products_ids(products_ids)

                # Verificando se há produtos vinculados a projetos
                linked_products = self.calculate_linked_products(sale, products)
                if linked_products:
                    return Response(
                        {
                            "detail": "A venda já possui projetos vinculados a alguns produtos.",
                            "linked_products": [
                                {"id": product.id, "name": product.name} for product in linked_products
                            ]
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Removendo produtos não enviados
                self.remove_unlinked_products(sale, products_ids)

                # Adicionando ou atualizando produtos na venda
                for product in products:
                    SaleProduct.objects.update_or_create(
                        sale=sale,
                        product=product,
                        defaults={
                            "amount": 1,
                            "value": product.product_value,
                            "reference_value": product.reference_value,
                            "cost_value": product.cost_value,
                        }
                    )

                # Recalculando o valor total da venda
                total_value = self.calculate_total_value(SaleProduct.objects.filter(sale=sale))
                sale.total_value = total_value
                sale.save()

            except serializers.ValidationError as e:
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {"detail": "Erro ao atualizar os produtos da venda.", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            # Removendo todos os produtos caso nenhum seja enviado
            SaleProduct.objects.filter(sale=sale).delete()

        # Retornando a resposta com os dados atualizados
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)
    
    def calculate_total_installment_value(self, sale, products):
        reference_value = sum(product.reference_value for product in products)
        print(f"Reference Value: {reference_value}")

        # Calcula a diferença de valor entre o total da venda e o valor de referência
        difference_value = sale.total_value - reference_value
        print(f"Difference Value: {difference_value}")

        # Calcula a margem de 7%
        if difference_value <= 0:
            margin_7 = Decimal("0.00")
            total_value = reference_value * (1 - sale.transfer_percentage / 100) - difference_value
            print(f"Margin 7 (<=0): {margin_7}")
        else:
            margin_7 = difference_value * Decimal("0.07")
            total_value = (reference_value * (1 - sale.transfer_percentage / 100)) + difference_value - margin_7
            print(f"Margin 7 (>0): {margin_7}")

        print(f"Total Value: {total_value}")
        return total_value
    
    def calculate_total_value(self, sales_products):
        total_value = 0
        for sales_product in sales_products:
            total_value += sales_product.value * sales_product.amount
        return total_value


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
        print("Sale ID:", sale_id)
        
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
        print("Commercial Proposal ID:", commercial_proposal_id)
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
                        print(salesproduct)
                        
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

