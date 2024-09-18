from logistics.models import *
from api.serializers.accounts import BaseSerializer
from .accounts import BranchSerializer
from .inspections import RoofTypeSerializer

class MaterialTypesSerializer(BaseSerializer):
      
      class Meta(BaseSerializer.Meta):
          model = MaterialTypes
          fields = '__all__'


class MaterialsSerializer(BaseSerializer):
  
      type = MaterialTypesSerializer()
      
      class Meta(BaseSerializer.Meta):
          model = Materials
          fields = '__all__'


class SolarEnergyKitSerializer(BaseSerializer):
  
      inversors_model = MaterialsSerializer()
      modules_model = MaterialsSerializer()
      branch = BranchSerializer()
      roof_type = RoofTypeSerializer()
      
      class Meta(BaseSerializer.Meta):
          model = SolarEnergyKit
          fields = '__all__'