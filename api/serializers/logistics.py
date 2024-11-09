from accounts.models import Branch
from inspections.models import RoofType
from logistics.models import *
from api.serializers.accounts import BaseSerializer
from .accounts import BranchSerializer
from .inspections import RoofTypeSerializer
from rest_framework.relations import PrimaryKeyRelatedField



class MaterialsSerializer(BaseSerializer):
    
    class Meta(BaseSerializer.Meta):
        model = Materials
        fields = '__all__'
        
        
class MaterialAttributesSerializer(BaseSerializer):      
     # Para leitura: usar serializador completo
     material = MaterialsSerializer(read_only=True)
     
     # Para escrita: usar apenas ID
     material_id = PrimaryKeyRelatedField(queryset=Materials.objects.all(), write_only=True, source='material')
    
        
     class Meta(BaseSerializer.Meta):
          model = MaterialAttributes
          fields = '__all__'


class SolarEnergyKitSerializer(BaseSerializer):
  
    # Para leitura: usar serializadores completos
    materials = MaterialsSerializer(many=True, read_only=True)
    branch = BranchSerializer(read_only=True)
    roof_type = RoofTypeSerializer(read_only=True)

    # Para escrita: usar apenas IDs
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, source='branch')
    roof_type_id = PrimaryKeyRelatedField(queryset=RoofType.objects.all(), write_only=True, source='roof_type')
      
    class Meta(BaseSerializer.Meta):
        model = SolarEnergyKit
        fields = '__all__'
      
        

class SolarKitMaterialsSerializer(BaseSerializer):
        
        # Para leitura: usar serializadores completos
        solar_kit = SolarEnergyKitSerializer(read_only=True)
        material = MaterialsSerializer(read_only=True)
        
        # Para escrita: usar apenas IDs
        solar_kit_id = PrimaryKeyRelatedField(queryset=SolarEnergyKit.objects.all(), write_only=True, source='solar_kit')
        material_id = PrimaryKeyRelatedField(queryset=Materials.objects.all(), write_only=True, source='material')
        
        class Meta(BaseSerializer.Meta):
            model = SolarKitMaterials
            fields = '__all__'
        

class SaleSolarKitSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = SaleSolarKits
        fields = '__all__'