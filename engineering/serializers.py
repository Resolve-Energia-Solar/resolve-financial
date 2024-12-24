from accounts.models import Address, User
from resolve_crm.serializers import SaleSerializer
from engineering.models import *
from api.serializers import BaseSerializer
from accounts.serializers import AddressSerializer, RelatedUserSerializer
from rest_framework.relations import PrimaryKeyRelatedField


class SituationEnergyCompanySerializer(BaseSerializer):
    class Meta:
        model = SituationEnergyCompany
        fields = '__all__'
        

class ResquestTypeSerializer(BaseSerializer):
    class Meta:
        model = ResquestType
        fields = '__all__'
    

class EnergyCompanySerializer(BaseSerializer):
    # Para leitura: usar serializador completo
    address = AddressSerializer(read_only=True)

    # Para escrita: usar apenas ID
    address_id = PrimaryKeyRelatedField(queryset=Address.objects.all(), write_only=True, source='address', required=False)

    class Meta:
        model = EnergyCompany
        exclude = ['is_deleted']
        

class ProjectReadSerializer(BaseSerializer):
    sale =  SaleSerializer(read_only=True)
    class Meta:
        model = Project
        fields = '__all__'


class SupplyAdequanceSerializer(BaseSerializer):
    class Meta:
        model = SupplyAdequance
        fields = '__all__'


class UnitsSerializer(BaseSerializer):
    supply_adquance = SupplyAdequanceSerializer(read_only=True, many=True)
    address = AddressSerializer(read_only=True)
    
    address_id = PrimaryKeyRelatedField(queryset=Address.objects.all(), write_only=True, source='address')
    supply_adquance_ids = PrimaryKeyRelatedField(queryset=SupplyAdequance.objects.all(), many=True, write_only=True, source='supply_adquance')
    project_id = PrimaryKeyRelatedField(queryset=Project.objects.all(), write_only=True, source='project')
    
    
    class Meta:
        model = Units
        fields = '__all__'


class RequestsEnergyCompanySerializer(BaseSerializer):
    # Para leitura: usar serializador completo
    company = EnergyCompanySerializer(read_only=True)
    project = ProjectReadSerializer(read_only=True)
    type = ResquestTypeSerializer(read_only=True)
    situation = SituationEnergyCompanySerializer(read_only=True, many=True)
    unit = UnitsSerializer(read_only=True)
    requested_by = RelatedUserSerializer(read_only=True)
    
    # Para escrita: usar apenas ID
    company_id = PrimaryKeyRelatedField(queryset=EnergyCompany.objects.all(), write_only=True, source='company')
    project_id = PrimaryKeyRelatedField(queryset=Project.objects.all(), write_only=True, source='project')
    type_id = PrimaryKeyRelatedField(queryset=ResquestType.objects.all(), write_only=True, source='type')
    situation_ids = PrimaryKeyRelatedField(queryset=SituationEnergyCompany.objects.all(), many=True, write_only=True, source='situation')
    unit_id = PrimaryKeyRelatedField(queryset=Units.objects.all(), write_only=True, source='unit')
    requested_by_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='requested_by')

    class Meta:
        model = RequestsEnergyCompany
        exclude = ['is_deleted']


class ReadRequestsEnergyCompanySerializer(BaseSerializer):
    company = EnergyCompanySerializer(read_only=True)
    type = ResquestTypeSerializer(read_only=True)
    situation = SituationEnergyCompanySerializer(read_only=True, many=True)
    unit = UnitsSerializer(read_only=True)
    requested_by = RelatedUserSerializer(read_only=True)
    
    class Meta:
        model = RequestsEnergyCompany
        exclude = ['is_deleted']