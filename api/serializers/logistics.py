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

    # Para escrita: usar apenas IDs
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, source='branch')
    roof_type_id = PrimaryKeyRelatedField(queryset=RoofType.objects.all(), write_only=True, source='roof_type', required=False)
    materials_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    sale_id = serializers.IntegerField(write_only=True, required=True)

    class Meta(BaseSerializer.Meta):
        model = Product
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        # Extraímos os IDs dos materiais e o sale_id antes de criar o produto
        materials_ids = validated_data.pop('materials_ids', [])
        sale_id = validated_data.pop('sale_id', None)

        # Validação do sale_id
        sale = Sale.objects.filter(id=sale_id).first()
        if not sale:
            raise serializers.ValidationError("Venda não encontrada.")

        # Criação do produto
        product = Product.objects.create(**validated_data)

        # Criação das relações com ProductMaterials
        ProductMaterials.objects.bulk_create([
            ProductMaterials(product=product, material_id=material_id)
            for material_id in materials_ids
        ])

        # Criação do relacionamento com SaleProduct
        self.create_sale_product(sale, product)

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        # Extraímos os IDs dos materiais e o sale_id antes de atualizar o produto
        materials_ids = validated_data.pop('materials_ids', [])
        sale_id = validated_data.pop('sale_id', None)

        # Validação do sale_id
        sale = Sale.objects.filter(id=sale_id).first()
        if not sale:
            raise serializers.ValidationError("Venda não encontrada.")

        # Atualização do produto
        instance = super().update(instance, validated_data)

        # Atualização das relações com ProductMaterials
        instance.materials.clear()
        ProductMaterials.objects.bulk_create([
            ProductMaterials(product=instance, material_id=material_id)
            for material_id in materials_ids
        ])

        # Atualização do relacionamento com SaleProduct
        self.create_sale_product(sale, instance)

        return instance

    def create_sale_product(self, sale, product):
        """Cria uma instância de SaleProduct associada à Sale e Product"""
        # Usando o SaleProductSerializer corretamente
        sale_product_serializer = SaleProductSerializer(
            data={
                'sale': sale.id,
                'product': product.id,
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
