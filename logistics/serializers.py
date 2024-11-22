from accounts.models import Branch
from inspections.models import RoofType
from logistics.models import *
from accounts.serializers import BaseSerializer
from resolve_crm.models import ComercialProposal, Sale
from accounts.serializers import BranchSerializer
from inspections.serializers import RoofTypeSerializer
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework import serializers
from django.db import transaction


class MaterialAttributesSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = MaterialAttributes
        fields = ['key', 'value']


class MaterialsSerializer(BaseSerializer):
    attributes = MaterialAttributesSerializer(many=True, required=False)

    class Meta(BaseSerializer.Meta):
        model = Materials
        fields = ['id', 'name', 'price', 'attributes']

    def create(self, validated_data):
        attributes_data = validated_data.pop('attributes', [])
        
        material = Materials.objects.create(**validated_data)
        
        for attribute_data in attributes_data:
            MaterialAttributes.objects.create(material=material, **attribute_data)
        
        return material

    def validate_price(self, value):
        if value is None or value == 0:
            raise serializers.ValidationError("O preço é obrigatório e deve ser maior que zero.")
        return value
        
        
class ProductMaterialsSerializer(BaseSerializer):
    material = MaterialsSerializer(read_only=True)
    material_id = PrimaryKeyRelatedField(queryset=Materials.objects.all(), write_only=True, source='material')

    class Meta(BaseSerializer.Meta):
        model = ProductMaterials
        fields = ['material', 'material_id', 'amount', 'id']


class ProductSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    materials = ProductMaterialsSerializer(many=True, read_only=True)
    branch = BranchSerializer(read_only=True)
    roof_type = RoofTypeSerializer(read_only=True)

    # Para escrita: usar apenas IDs com quantidade
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, source='branch')
    roof_type_id = PrimaryKeyRelatedField(queryset=RoofType.objects.all(), write_only=True, source='roof_type', required=False)
    materials_ids = serializers.ListField(
        child=serializers.DictField(
            child=serializers.DecimalField(max_digits=20, decimal_places=6),
            help_text="Lista de materiais com `id` e `amount`."
        ),
        write_only=True,
        required=False
    )
    sale_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    commercial_proposal_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta(BaseSerializer.Meta):
        model = Product
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        # Extraímos os materiais com quantidade
        materials_data = validated_data.pop('materials_ids', [])
        sale_id = validated_data.pop('sale_id', None)
        commercial_proposal_id = validated_data.pop('commercial_proposal_id', None)
        if sale_id:
            # Validação do sale_id
            sale = Sale.objects.filter(id=sale_id).first()
            if not sale:
                raise serializers.ValidationError("Venda não encontrada.")
        if commercial_proposal_id:
            # Validação do commercial_proposal_id
            try:
                commercial_proposal = ComercialProposal.objects.get(id=commercial_proposal_id)
            except ComercialProposal.DoesNotExist:
                raise serializers.ValidationError("Proposta comercial não encontrada.")
            

        # Criação do produto
        product = Product.objects.create(**validated_data)

        # Criação das relações com ProductMaterials
        self.create_or_update_materials(product, materials_data)

        # Criação do relacionamento com SaleProduct
        if sale_id:
            self.create_sale_product(sale, product)
            
        if commercial_proposal_id:
            self.create_comercial_product(commercial_proposal, product)

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        # Extraímos os materiais com quantidade
        materials_data = validated_data.pop('materials_ids', [])
        sale_id = validated_data.pop('sale_id', None)
        commercial_proposal_id = validated_data.pop('commercial_proposal_id', None)
        
        if commercial_proposal_id:
            # Validação do commercial_proposal_id
            try:
                commercial_proposal = ComercialProposal.objects.get(id=commercial_proposal_id)
            except ComercialProposal.DoesNotExist:
                raise serializers.ValidationError("Proposta comercial não encontrada.")
        
        if sale_id:
            # Validação do sale_id
            sale = Sale.objects.filter(id=sale_id).first()
            if not sale:
                raise serializers.ValidationError("Venda não encontrada.")

        # Atualização do produto
        instance = super().update(instance, validated_data)

        # Atualização das relações com ProductMaterials
        self.create_or_update_materials(instance, materials_data)

        # Atualização do relacionamento com SaleProduct
        if sale_id:
            self.create_sale_product(sale, instance)
            
        if commercial_proposal_id:
            self.create_comercial_product(commercial_proposal, instance)

        return instance

    def create_or_update_materials(self, product, materials_data):
        """
        Atualiza ou cria os materiais associados ao produto e remove os que não estão no payload.
        """
        # Obter IDs de materiais existentes para o produto
        existing_material_ids = set(ProductMaterials.objects.filter(product=product).values_list('id', flat=True))

        # Obter IDs de materiais enviados no payload
        payload_material_ids = set(material.get('id') for material in materials_data if material.get('id'))

        # Identificar IDs que precisam ser removidos (existentes, mas não enviados no payload)
        materials_to_remove = existing_material_ids - payload_material_ids

        # Excluir materiais que não estão no payload
        if materials_to_remove:
            ProductMaterials.objects.filter(id__in=materials_to_remove).delete()

        # Processar materiais enviados no payload
        for material_data in materials_data:
            line_id = material_data.get('id')  # ID da linha intermediária
            material_id = material_data.get('material_id')  # ID do material
            amount = material_data.get('amount')  # Quantidade

            if not material_id or amount is None:
                raise serializers.ValidationError("Cada material deve ter `material_id` e `amount`.")

            # Obter o material
            material = Materials.objects.filter(id=material_id).first()
            if not material:
                raise serializers.ValidationError(f"Material com ID {material_id} não encontrado.")

            if line_id:
                # Atualizar a linha intermediária existente
                product_material = ProductMaterials.objects.filter(id=line_id, product=product).first()
                if not product_material:
                    raise serializers.ValidationError(f"Linha intermediária com ID {line_id} não encontrada para este produto.")

                # Atualizar os valores da linha existente
                product_material.material = material
                product_material.amount = amount
                product_material.save()
            else:
                # Criar uma nova linha intermediária
                ProductMaterials.objects.create(
                    product=product,
                    material=material,
                    amount=amount
                )

    
    def create_comercial_product(self, proposal, product):
        """Cria uma instância de ComercialProduct associada à ComercialProposal e Product"""
        comercial_product_serializer = SaleProductSerializer(
            data={
                'commercial_proposal_id': proposal.id,
                'product_id': product.id,
                'value': product.product_value,
                'reference_value': product.reference_value,
                'cost_value': product.cost_value,
                'amount': 1
            }
        )

        # Verificar se os dados são válidos antes de salvar
        if comercial_product_serializer.is_valid():
            comercial_product_serializer.save()
        else:
            raise serializers.ValidationError(comercial_product_serializer.errors)


    def create_sale_product(self, sale, product):
        """Cria uma instância de SaleProduct associada à Sale e Product"""
        sale_product_serializer = SaleProductSerializer(
            data={
                'sale_id': sale.id,
                'product_id': product.id,
                'value': product.product_value,
                'reference_value': product.reference_value,
                'cost_value': product.cost_value,
                'amount': 1
            }
        )

        # Verificar se os dados são válidos antes de salvar
        if sale_product_serializer.is_valid():
            sale_product_serializer.save()
        else:
            raise serializers.ValidationError(sale_product_serializer.errors)


class SaleProductSerializer(BaseSerializer):
    
    product_id = PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True, source='product')
    sale_id = PrimaryKeyRelatedField(queryset=Sale.objects.all(), write_only=True, source='sale')
    commercial_proposal_id = PrimaryKeyRelatedField(queryset=ComercialProposal.objects.all(), write_only=True, source='commercial_proposal', required=False)
    
    class Meta(BaseSerializer.Meta):
        model = SaleProduct
        fields = '__all__'
        

class ProjectMaterialsSerializer(BaseSerializer):
    material = MaterialsSerializer(read_only=True)
    material_id = PrimaryKeyRelatedField(queryset=Materials.objects.all(), source='material', write_only=True)
    
    class Meta:
        model = ProjectMaterials
        fields = ['material', 'material_id', 'amount', 'is_exit', 'serial_number']
