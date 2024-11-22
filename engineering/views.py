from api.views import BaseModelViewSet
from .models import *
from .serializers import *


class SupplyAdequanceViewSet(BaseModelViewSet):
    queryset = SupplyAdequance.objects.all()
    serializer_class = SupplyAdequanceSerializer


class ResquestTypeViewSet(BaseModelViewSet):
    queryset = ResquestType.objects.all()
    serializer_class = ResquestTypeSerializer
    
    
class SituationEnergyCompanyViewSet(BaseModelViewSet):
    queryset = SituationEnergyCompany.objects.all()
    serializer_class = SituationEnergyCompanySerializer


class EnergyCompanyViewSet(BaseModelViewSet):
    queryset = EnergyCompany.objects.all()
    serializer_class = EnergyCompanySerializer


class RequestsEnergyCompanyViewSet(BaseModelViewSet):
    queryset = RequestsEnergyCompany.objects.all()
    serializer_class = RequestsEnergyCompanySerializer
    

class UnitsViewSet(BaseModelViewSet):
    queryset = Units.objects.all()
    serializer_class = UnitsSerializer
