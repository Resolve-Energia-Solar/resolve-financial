from accounts.models import Branch
from inspections.models import RoofType
from logistics.models import *
from api.serializers.accounts import BaseSerializer
from .accounts import BranchSerializer
from .inspections import RoofTypeSerializer
from rest_framework.relations import PrimaryKeyRelatedField

class MaterialAttributesSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = MaterialAttributes
        fields = ['key', 'value']


class MaterialsSerializer(BaseSerializer):
    attributes = MaterialAttributesSerializer(many=True, read_only=True)

    class Meta(BaseSerializer.Meta):
        model = Materials
        fields = ['id', 'name', 'price', 'attributes']
        
        
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
    roof_type_id = PrimaryKeyRelatedField(queryset=RoofType.objects.all(), write_only=True, source='roof_type')

    class Meta(BaseSerializer.Meta):
        model = Product
        fields = ['id', 'name', 'description', 'product_value', 'reference_value', 
                  'cost_value', 'branch', 'branch_id', 'roof_type', 'roof_type_id', 'materials']


class SaleProductSerializer(BaseSerializer):
    product = ProductSerializer(read_only=True)
    class Meta(BaseSerializer.Meta):
        model = SaleProduct
        fields = '__all__'