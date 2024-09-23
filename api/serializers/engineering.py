from accounts.models import Address
from engineering.models import EnergyCompany, RequestsEnergyCompany, CircuitBreaker, Units
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


class CircuitBreakerSerializer(BaseSerializer):
    
    # Para leitura: usar serializador completo
    # material = MaterialsSerializer(read_only=True)
    
    # Para escrita: usar apenas ID
    # material_id = PrimaryKeyRelatedField(queryset=Materials.objects.all(), write_only=True, source='material')

    class Meta:
        model = CircuitBreaker
        exclude = ['is_deleted']

class UnitsSerializer(BaseSerializer):
    
    address = AddressSerializer(read_only=True)
    
    class Meta:
        model = Units
        fields = '__all__'

