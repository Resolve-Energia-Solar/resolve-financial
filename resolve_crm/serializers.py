from django.forms import ValidationError
from accounts.models import Address, User
from core.models import Column
from engineering.models import Units
from resolve_crm.models import *
from accounts.serializers import RelatedUserSerializer, AddressSerializer,  ContentTypeSerializer, BranchSerializer
from api.serializers import BaseSerializer
from logistics.serializers import ProductSerializer
from logistics.models import Materials, ProjectMaterials, Product, SaleProduct
from rest_framework.serializers import PrimaryKeyRelatedField, SerializerMethodField, ListField, DictField
from logistics.serializers import ProjectMaterialsSerializer, SaleProductSerializer


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
    

class SaleSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    customer = RelatedUserSerializer(read_only=True)
    seller = RelatedUserSerializer(read_only=True)
    sales_supervisor = RelatedUserSerializer(read_only=True)
    sales_manager = RelatedUserSerializer(read_only=True)
    branch = BranchSerializer(read_only=True)
    marketing_campaign = MarketingCampaignSerializer(read_only=True)
    missing_documents = SerializerMethodField()
    sale_products = SaleProductSerializer(source='saleproduct_set', many=True, read_only=True)
    can_generate_contract = SerializerMethodField()
    total_paid = SerializerMethodField()

    # Para escrita: usar apenas IDs
    customer_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='customer')
    seller_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='seller')
    sales_supervisor_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='sales_supervisor')
    sales_manager_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='sales_manager')
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, source='branch')
    marketing_campaign_id = PrimaryKeyRelatedField(queryset=MarketingCampaign.objects.all(), write_only=True, source='marketing_campaign', required=False)
    # products_ids = PrimaryKeyRelatedField(queryset=Product.objects.all(), many=True, write_only=True, source='products', required=False)
    # commercial_proposal_id = PrimaryKeyRelatedField(queryset=ComercialProposal.objects.all(), write_only=True, source='comercial_proposal', required=False)

    class Meta:
        model = Sale
        fields = '__all__'

    def get_missing_documents(self, obj):
        return obj.missing_documents()
    
    def get_can_generate_contract(self, obj):
        return "true" if obj.can_generate_contract else "false"

    
    def get_total_paid(self, obj):
        return obj.total_paid

    # def create(self, validated_data):
    #     products_ids = validated_data.pop('products_ids', [])
    #     comercial_proposal = validated_data.pop('comercial_proposal', None)
    #     print("comercial_proposal", comercial_proposal)
    #     print("products_ids", products_ids)

    #     # Criação da venda
    #     sale = super().create(validated_data)
        
    #     if comercial_proposal:
    #         # Vincular SaleProducts da proposta comercial à nova venda
    #         sale_products = SaleProduct.objects.filter(commercial_proposal=comercial_proposal, sale__isnull=True)
    #         for sale_product in sale_products:
    #             sale_product.sale = sale
    #             sale_product.save()
    #     else:
    #         # Criar novos SaleProduct para os produtos fornecidos
    #         for product_id in products_ids:
    #             product = Product.objects.get(id=product_id)
    #             SaleProduct.objects.create(
    #                 sale=sale,
    #                 product=product,
    #                 amount=1,
    #                 value=product.product_value,
    #                 reference_value=product.reference_value,
    #                 cost_value=product.cost_value
    #             )
        
    #     if sale.total_value == 0:
    #         saleproducts = SaleProduct.objects.filter(sale=sale)
    #         total_value = 0
    #         for saleproduct in saleproducts:
    #             value = saleproduct.value * saleproduct.amount
    #             total_value += value
                
    #         sale.total_value = total_value
    #         sale.save()
                
                
    #     print("sale", sale)
    #     return sale


class ProjectSerializer(BaseSerializer):
    # Para leitura
    sale = SaleSerializer(read_only=True)
    designer = RelatedUserSerializer(read_only=True)
    homologator = RelatedUserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    materials = ProjectMaterialsSerializer(source='projectmaterials_set', many=True, read_only=True)

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
    proposal_products = SaleProductSerializer(source='saleproduct_set', many=True, read_only=True)

    lead_id = PrimaryKeyRelatedField(queryset=Lead.objects.all(), write_only=True, source='lead')
    created_by_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='created_by')

    class Meta:
        model = ComercialProposal
        fields = '__all__'


class ContractSubmissionSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    sale = SaleSerializer(read_only=True)

    # Para escrita: usar apenas IDs
    sale_id = PrimaryKeyRelatedField(queryset=Sale.objects.all(), write_only=True, source='sale')

    class Meta:
        model = ContractSubmission
        fields = '__all__'
