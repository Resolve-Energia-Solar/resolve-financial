from accounts.models import Branch
from inspections.models import RoofType
from logistics.models import *
from api.serializers.accounts import BaseSerializer
from resolve_crm.models import Project, Sale
from .accounts import BranchSerializer
from .inspections import RoofTypeSerializer
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
        fields = ['material', 'material_id', 'amount']


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
    sale_id = serializers.IntegerField(write_only=True, required=False)

    class Meta(BaseSerializer.Meta):
        model = Product
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        # Extraímos os materiais com quantidade
        materials_data = validated_data.pop('materials_ids', [])
        sale_id = validated_data.pop('sale_id', None)
        if sale_id:
            # Validação do sale_id
            sale = Sale.objects.filter(id=sale_id).first()
            if not sale:
                raise serializers.ValidationError("Venda não encontrada.")

        # Criação do produto
        product = Product.objects.create(**validated_data)

        # Criação das relações com ProductMaterials
        self.create_or_update_materials(product, materials_data)

        # Criação do relacionamento com SaleProduct
        if sale_id:
            self.create_sale_product(sale, product)

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        # Extraímos os materiais com quantidade
        materials_data = validated_data.pop('materials_ids', [])
        sale_id = validated_data.pop('sale_id', None)
        
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

        return instance

    def create_or_update_materials(self, product, materials_data):
        """
        Cria ou atualiza as relações na tabela intermediária ProductMaterials
        com base nos materiais e suas quantidades fornecidas.
        """
        for material_data in materials_data:
            material_id = material_data.get('id')
            amount = material_data.get('amount')

            if not material_id or amount is None:
                raise serializers.ValidationError("Cada material deve ter `id` e `amount`.")

            material = Materials.objects.filter(id=material_id).first()
            if not material:
                raise serializers.ValidationError(f"Material com ID {material_id} não encontrado.")

            # Atualizar ou criar o relacionamento na tabela intermediária
            ProductMaterials.objects.update_or_create(
                product=product,
                material=material,
                defaults={'amount': amount}
            )

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

    # from .resolve_crm import SaleSerializer

    product = ProductSerializer(read_only=True)
    # sale = SaleSerializer(read_only=True)
    
    product_id = PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True, source='product')
    sale_id = PrimaryKeyRelatedField(queryset=Sale.objects.all(), write_only=True, source='sale')
    
    class Meta(BaseSerializer.Meta):
        model = SaleProduct
        fields = '__all__'
        

class ProjectMaterialsSerializer(BaseSerializer):
    material = MaterialsSerializer(read_only=True)
    material_id = PrimaryKeyRelatedField(queryset=Materials.objects.all(), source='material', write_only=True)
    
    class Meta:
        model = ProjectMaterials
        fields = ['material', 'material_id', 'amount', 'is_exit', 'serial_number']
