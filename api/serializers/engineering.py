from accounts.models import Address
from engineering.models import EnergyCompany, RequestsEnergyCompany, SupplyAdequance, Units
from .accounts import BaseSerializer, AddressSerializer
from rest_framework.relations import PrimaryKeyRelatedField
# from .resolve_crm import ProjectSerializer
# from .logistics import MaterialsSerializer


class EnergyCompanySerializer(BaseSerializer):
    # Para leitura: usar serializador completo
    address = AddressSerializer(read_only=True)

    # Para escrita: usar apenas ID
    address_id = PrimaryKeyRelatedField(queryset=Address.objects.all(), write_only=True, source='address')

    class Meta:
        model = EnergyCompany
        exclude = ['is_deleted']


class RequestsEnergyCompanySerializer(BaseSerializer):
    # Para leitura: usar serializador completo
    company = EnergyCompanySerializer(read_only=True)
    # project = ProjectSerializer()
    
    # Para escrita: usar apenas ID
    company_id = PrimaryKeyRelatedField(queryset=EnergyCompany.objects.all(), write_only=True, source='company')
    # project_id = PrimaryKeyRelatedField(queryset=Project.objects.all(), write_only=True, source='project')

    class Meta:
        model = RequestsEnergyCompany
        exclude = ['is_deleted']


class SupplyAdequanceSerializer(BaseSerializer):
    class Meta:
        model = SupplyAdequance
        fields = '__all__'


class UnitsSerializer(BaseSerializer):
    supply_adquance = SupplyAdequanceSerializer(read_only=True, many=True)
    address = AddressSerializer(read_only=True)
    
    address_id = PrimaryKeyRelatedField(queryset=Address.objects.all(), write_only=True, source='address')
    supply_adquance_ids = PrimaryKeyRelatedField(queryset=SupplyAdequance.objects.all(), many=True, write_only=True, source='supply_adquance')
    
    
    class Meta:
        model = Units
        fields = '__all__'
