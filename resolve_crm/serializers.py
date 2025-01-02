from django.forms import ValidationError
from accounts.models import Address, User
from core.models import Column
from core.serializers import AttachmentSerializer
from engineering.models import Units
from financial.models import FranchiseInstallment
from resolve_crm.models import *
from accounts.serializers import RelatedUserSerializer, AddressSerializer,  ContentTypeSerializer, BranchSerializer
from api.serializers import BaseSerializer
from logistics.serializers import ProductSerializer
from logistics.models import Materials, ProjectMaterials, Product, SaleProduct
from rest_framework.serializers import PrimaryKeyRelatedField, SerializerMethodField, ListField, DictField
from logistics.serializers import ProjectMaterialsSerializer, SaleProductSerializer
import re


class OriginSerializer(BaseSerializer):
    class Meta:
        model = Origin
        fields = '__all__'
      
        
class ReadSalesSerializer(BaseSerializer):
    missing_documents = SerializerMethodField()
    can_generate_contract = SerializerMethodField()
    total_paid = SerializerMethodField()

    class Meta:
        model = Sale
        fields = ['id', 'total_value', 'status', 'total_paid', 'missing_documents', 'can_generate_contract']

    def get_missing_documents(self, obj):
        return obj.missing_documents()
    
    def get_can_generate_contract(self, obj):
        return "true" if obj.can_generate_contract else "false"

    def get_total_paid(self, obj):
        return obj.total_paid

 
class LeadSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    customer = RelatedUserSerializer(read_only=True)
    seller = RelatedUserSerializer(read_only=True, allow_null=True)
    sdr = RelatedUserSerializer(read_only=True, allow_null=True)
    addresses = AddressSerializer(many=True, read_only=True)
    # column = ColumnSerializer(read_only=True)
    origin = OriginSerializer(read_only=True)
    sales = SerializerMethodField()
    proposals = SerializerMethodField()
    

    # Para escrita: usar apenas IDs
    seller_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='seller', allow_null=True, required=False)
    sdr_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='sdr', allow_null=True, required=False)
    addresses_ids = PrimaryKeyRelatedField(queryset=Address.objects.all(), many=True, write_only=True, source='addresses', required=False)
    column_id = PrimaryKeyRelatedField(queryset=Column.objects.all(), write_only=True, source='column', required=False)
    origin_id = PrimaryKeyRelatedField(queryset=Origin.objects.all(), write_only=True, source='origin')


    class Meta:
        model = Lead
        depth = 1
        fields = '__all__'
        
    def validate(self, data):
        phone = data.get('phone')
        if phone and len(re.sub(r'\D', '', phone)) != 11:
            raise ValidationError({'phone': 'Phone number must have exactly 11 digits.'})
        return data
        
    def get_sales(self, obj):
        # Aqui, obtenha as vendas vinculadas ao usuário do lead (exemplo para seller)
        if obj.customer:
            sales = Sale.objects.filter(customer=obj.customer)
            return ReadSalesSerializer(sales, many=True).data
        return []
    
    def get_proposals(self, obj):
        proposals = ComercialProposal.objects.filter(lead=obj)
        return [proposal.id for proposal in proposals]


class LeadTaskSerializer(BaseSerializer):
    
    # Para leitura: usar serializadores completos  
    members = RelatedUserSerializer(many=True, read_only=True)
    # lead = LeadSerializer(read_only=True)
    
    # Para escrita: usar apenas IDs
    members_ids = PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, write_only=True, source='members')
    # lead_id = PrimaryKeyRelatedField(queryset=Lead.objects.all(), write_only=True, source='lead')
    
    class Meta:
        model = Task
        fields = '__all__'


class MarketingCampaignSerializer(BaseSerializer):
    
    class Meta:
        model = MarketingCampaign
        fields = '__all__'
        
        
class ReadProjectSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    designer = RelatedUserSerializer(read_only=True)
    homologator = RelatedUserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    materials = ProjectMaterialsSerializer(source='projectmaterials_set', many=True, read_only=True)
    requests_energy_company = SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'designer', 'homologator', 'product', 'materials', 'requests_energy_company']
        depth = 1

    def get_requests_energy_company(self, obj):
        from engineering.serializers import ReadRequestsEnergyCompanySerializer
        requests = obj.requests_energy_company.all()
        return ReadRequestsEnergyCompanySerializer(requests, many=True).data
    

class SaleSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    customer = RelatedUserSerializer(read_only=True)
    seller = RelatedUserSerializer(read_only=True)
    sales_supervisor = RelatedUserSerializer(read_only=True)
    sales_manager = RelatedUserSerializer(read_only=True)
    branch = BranchSerializer(read_only=True)
    marketing_campaign = MarketingCampaignSerializer(read_only=True)
    missing_documents = SerializerMethodField()
    sale_products = SaleProductSerializer(many=True, read_only=True)
    can_generate_contract = SerializerMethodField()
    total_paid = SerializerMethodField()
    
    projects = ReadProjectSerializer(many=True, read_only=True)

    # Para escrita: usar apenas IDs
    customer_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='customer')
    seller_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='seller')
    sales_supervisor_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='sales_supervisor')
    sales_manager_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='sales_manager')
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, source='branch')
    marketing_campaign_id = PrimaryKeyRelatedField(queryset=MarketingCampaign.objects.all(), write_only=True, source='marketing_campaign', required=False)
    products_ids = PrimaryKeyRelatedField(queryset=Product.objects.all(), many=True, write_only=True, required=False)
    commercial_proposal_id = PrimaryKeyRelatedField(queryset=ComercialProposal.objects.all(), write_only=True, required=False)
    
    class Meta:
        model = Sale
        fields = '__all__'
        

    def create(self, validated_data):
        products_ids = validated_data.pop('products_ids', [])
        commercial_proposal_id = validated_data.pop('commercial_proposal_id', None)
        sale = super().create(validated_data)

        self._handle_products(sale, products_ids, commercial_proposal_id)
        return sale

    def update(self, instance, validated_data):
        products_ids = validated_data.pop('products_ids', None)
        commercial_proposal_id = validated_data.pop('commercial_proposal_id', None)
        sale = super().update(instance, validated_data)

        if products_ids is not None or commercial_proposal_id is not None:
            SaleProduct.objects.filter(sale=sale).delete()
            self._handle_products(sale, products_ids or [], commercial_proposal_id)

        return sale

    def _handle_products(self, sale, products_ids, commercial_proposal_id):
        products_list = []

        if commercial_proposal_id:
            try:
                commercial_proposal = ComercialProposal.objects.get(id=commercial_proposal_id)
                sale_products = SaleProduct.objects.filter(commercial_proposal=commercial_proposal)

                if not sale_products.exists():
                    raise ValidationError({"detail": "Proposta comercial não possui produtos associados."})

                if sale_products.filter(sale__isnull=False).exists():
                    raise ValidationError({"detail": "Proposta comercial já vinculada a uma venda."})

                for sale_product in sale_products:
                    sale_product.sale = sale
                    sale_product.save()
                    products_list.append(sale_product)

            except ComercialProposal.DoesNotExist:
                raise ValidationError({"detail": "Proposta comercial não encontrada."})
        else:
            products = self.validate_products_ids(products_ids)
            for product in products:
                sale_product = SaleProduct.objects.create(
                    sale=sale,
                    product=product,
                    amount=1,
                    value=product.product_value,
                    reference_value=product.reference_value,
                    cost_value=product.cost_value,
                )
                products_list.append(sale_product)
                
        self.create_projects(sale, products_list)

        # Recalcular valores da venda, se necessário
        if sale.total_value is None or sale.total_value == 0:
            total_value = self.calculate_total_value(products_list)
            sale.total_value = total_value
            sale.save()

        if sale.sale_products.exists():
            total_installment_value = self.calculate_total_installment_value(sale, sale.sale_products.all())
            if sale.total_value:
                FranchiseInstallment.objects.create(
                    sale=sale,
                    installment_value=total_installment_value,
                )
                
    def create_projects(self, sale, products):
        for product in products:
            project = Project.objects.create(
                sale=sale,
                product=product.product,
            )
            try:
                project.save()
            except Exception as e:
                raise ValidationError({"detail": f"Erro ao criar projeto para o produto {product.name}: {e}"})
            
            

    def validate_products_ids(self, products_ids):
        products = []
        for product_id in products_ids:
            if isinstance(product_id, Product):
                products.append(product_id)  # Já é uma instância do modelo
            else:
                try:
                    product = Product.objects.get(id=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    raise ValidationError({"detail": f"Produto com ID {product_id} não encontrado."})
        return products

    def calculate_total_value(self, sale_products):
        total_value = 0
        for sp in sale_products:
            total_value += sp.value * sp.amount
        return total_value

    def calculate_total_installment_value(self, sale, products):
        from decimal import Decimal
        reference_value = sum(p.reference_value for p in products)
        difference_value = sale.total_value - reference_value

        if difference_value <= 0:
            if sale.transfer_percentage:
                total_value = reference_value * (1 - sale.transfer_percentage / 100) - difference_value
            else:
                total_value = reference_value * (1 - sale.branch.transfer_percentage / 100) + difference_value
        else:
            margin_7 = difference_value * Decimal("0.07")
            if sale.transfer_percentage:
                total_value = (reference_value * (1 - sale.transfer_percentage / 100)) + difference_value - margin_7
            else:
                total_value = (reference_value * (1 - sale.branch.transfer_percentage / 100)) + difference_value - margin_7

        return total_value
    
    def get_missing_documents(self, obj):
        return obj.missing_documents()
    
    def get_can_generate_contract(self, obj):
        return obj.can_generate_contract

    def get_total_paid(self, obj):
        return obj.total_paid


class ReadSaleSerializer(BaseSerializer):
    can_generate_contract = SerializerMethodField()
    total_paid = SerializerMethodField()
    
    projects = ReadProjectSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = '__all__'
        depth = 1

    
    def get_can_generate_contract(self, obj):
        return obj.can_generate_contract

    def get_total_paid(self, obj):
        return obj.total_paid


class ProjectSerializer(BaseSerializer):
    # Para leitura
    # sale = ReadSaleSerializer(read_only=True)
    # designer = RelatedUserSerializer(read_only=True)
    # homologator = RelatedUserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    materials = ProjectMaterialsSerializer(source='projectmaterials_set', many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    is_released_to_engineering = SerializerMethodField()
    documents_under_analysis = SerializerMethodField()
    field_services = SerializerMethodField()
    requests_energy_company = SerializerMethodField()
    access_opinion = SerializerMethodField()
    address = SerializerMethodField()

    # Para escrita
    sale_id = PrimaryKeyRelatedField(queryset=Sale.objects.all(), write_only=True, source='sale', required=True)
    homologator_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='homologator', required=False)
    product_id = PrimaryKeyRelatedField(queryset=Product.objects.filter(id__in=SaleProduct.objects.values_list('product_id', flat=True)), write_only=True, source='product', required=False)
    units_ids = PrimaryKeyRelatedField(queryset=Units.objects.all(), many=True, write_only=True, source='units', required=False)
    
    # Lista de materiais com detalhes
    materials_data = ListField(
        child= DictField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Project
        fields = '__all__'
        depth = 1
    
    def get_address(self, obj):
        if obj.address:
            return AddressSerializer(obj.address).data
        return None
    
    def get_access_opinion(self, obj):
        return obj.access_opinion()    
        
    def get_is_released_to_engineering(self, obj):
        return obj.is_released_to_engineering()
    
    def get_documents_under_analysis(self, obj):
        documents = obj.documents_under_analysis.all()
        return AttachmentSerializer(documents, many=True).data
    
    def get_field_services(self, obj):
        field_services = obj.field_services.values_list('id', flat=True)
        return list(field_services)
    
    def get_requests_energy_company(self, obj):
        from engineering.serializers import ReadRequestsEnergyCompanySerializer
        requests = obj.requests_energy_company.all()
        return ReadRequestsEnergyCompanySerializer(requests, many=True).data
    
    def update(self, instance, validated_data):
        # Extrair dados de materiais e endereços
        materials_data = validated_data.pop('materials_data', [])
        
        # Atualiza os campos do projeto
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Atualiza materiais se fornecidos
        if materials_data:
            self._save_materials(instance, materials_data)

        return instance


    def _save_materials(self, project, materials_data):
        """Função auxiliar para criar ou atualizar materiais do projeto com detalhes extras"""
        project.materials.clear()  # Limpar materiais antigos
        for material_data in materials_data:
            material_id = material_data.get('material_id')
            amount = material_data.get('amount', 1)
            is_exit = material_data.get('is_exit', False)
            serial_number = material_data.get('serial_number', None)

            # Verificar se o material existe
            try:
                material = Materials.objects.get(id=material_id)
            except Materials.DoesNotExist:
                raise ValidationError({'detail': f'Material com id {material_id} não encontrado.'}, code=404)

            ProjectMaterials.objects.create(
                project=project,
                material=material,
                amount=amount,
                is_exit=is_exit,
                serial_number=serial_number
        )
            

class ComercialProposalSerializer(BaseSerializer):
    lead = LeadSerializer(read_only=True)
    created_by = RelatedUserSerializer(read_only=True)
    commercial_products = SaleProductSerializer(many=True, read_only=True)

    lead_id = PrimaryKeyRelatedField(queryset=Lead.objects.all(), write_only=True, source='lead')
    created_by_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='created_by')
    commercial_products_ids = PrimaryKeyRelatedField(queryset=Product.objects.all(), many=True, write_only=True, source='commercial_products', required=False)

    class Meta:
        model = ComercialProposal
        fields = '__all__'

    def create(self, validated_data):
        # Extrair os dados relacionados aos produtos
        products_data = validated_data.pop('commercial_products', [])
        proposal = super().create(validated_data)
        
        # Criar entradas na tabela intermediária
        for product in products_data:
            SaleProduct.objects.create(
                commercial_proposal=proposal,
                product=product,
                amount=1,  # Pode ser customizado conforme necessário
                cost_value=product.cost_value,  # Substitua por lógica para obter o valor
                reference_value=product.reference_value,  # Ajuste conforme necessário
                value = product.product_value
            )

        return proposal

    def update(self, instance, validated_data):
        # Extrair os dados relacionados aos produtos
        products_data = validated_data.pop('commercial_products', [])
        proposal = super().update(instance, validated_data)

        # Limpar produtos antigos relacionados
        SaleProduct.objects.filter(commercial_proposal=instance).delete()

        # Criar novas entradas na tabela intermediária
        for product in products_data:
            SaleProduct.objects.create(
                commercial_proposal=proposal,
                product=product,
                amount=1,  # Pode ser customizado conforme necessário
                cost_value=product.cost_value,  # Substitua por lógica para obter o valor
                reference_value=product.reference_value,  # Ajuste conforme necessário
                value = product.product_value
            )

        return proposal


class ContractSubmissionSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    sale = SaleSerializer(read_only=True)

    # Para escrita: usar apenas IDs
    sale_id = PrimaryKeyRelatedField(queryset=Sale.objects.all(), write_only=True, source='sale')

    class Meta:
        model = ContractSubmission
        fields = '__all__'
