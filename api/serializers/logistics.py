from accounts.models import Branch
from inspections.models import RoofType
from logistics.models import *
from api.serializers.accounts import BaseSerializer
from .accounts import BranchSerializer
from .inspections import RoofTypeSerializer
from rest_framework.relations import PrimaryKeyRelatedField


class MaterialTypesSerializer(BaseSerializer):
      
      class Meta(BaseSerializer.Meta):
          model = MaterialTypes
          fields = '__all__'


class MaterialsSerializer(BaseSerializer):
  
    # Para leitura: usar serializador completo
    type = MaterialTypesSerializer(read_only=True)
    
    # Para escrita: usar apenas ID
    type_id = PrimaryKeyRelatedField(queryset=MaterialTypes.objects.all(), write_only=True, source='type')

      
    class Meta(BaseSerializer.Meta):
        model = Materials
        fields = '__all__'


class SolarEnergyKitSerializer(BaseSerializer):
  
    # Para leitura: usar serializadores completos
    inversors_model = MaterialsSerializer(read_only=True)
    modules_model = MaterialsSerializer(read_only=True)
    branch = BranchSerializer(read_only=True)
    roof_type = RoofTypeSerializer(read_only=True)

    # Para escrita: usar apenas IDs
    inversors_model_id = PrimaryKeyRelatedField(queryset=Materials.objects.all(), write_only=True, source='inversors_model')
    modules_model_id = PrimaryKeyRelatedField(queryset=Materials.objects.all(), write_only=True, source='modules_model')
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, source='branch')
    roof_type_id = PrimaryKeyRelatedField(queryset=RoofType.objects.all(), write_only=True, source='roof_type')
      
    class Meta(BaseSerializer.Meta):
        model = SolarEnergyKit
        fields = '__all__'

