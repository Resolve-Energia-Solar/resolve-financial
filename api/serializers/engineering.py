from engineering.models import EnergyCompany, RequestsEnergyCompany, CircuitBreaker, Units
from .accounts import BaseSerializer, AddressSerializer
# from .resolve_crm import ProjectSerializer
# from .logistics import MaterialsSerializer

class EnergyCompanySerializer(BaseSerializer):
    address = AddressSerializer()

    class Meta:
        model = EnergyCompany
        exclude = ['is_deleted']


class RequestsEnergyCompanySerializer(BaseSerializer):
    company = EnergyCompanySerializer()
    # project = ProjectSerializer()

    class Meta:
        model = RequestsEnergyCompany
        exclude = ['is_deleted']


class CircuitBreakerSerializer(BaseSerializer):
    
    # material = MaterialsSerializer()

    class Meta:
        model = CircuitBreaker
        exclude = ['is_deleted']

class UnitsSerializer(BaseSerializer):
    
    class Meta:
        model = Units
        fields = '__all__'


class UnitBillSerializer(BaseSerializer):
    
    class Meta:
        model = Units
        fields = ['name', 'bill_file']