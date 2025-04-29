from api.urls import router
from engineering.views import *


router.register('energy-companies', EnergyCompanyViewSet, basename='energycompany')
router.register('requests-energy-companies', RequestsEnergyCompanyViewSet, basename='requestsenergycompany')
router.register('units', UnitsViewSet, basename='unit')
router.register('supply-adequances', SupplyAdequanceViewSet, basename='supply-adequance')
router.register('situation-energy-companies', SituationEnergyCompanyViewSet, basename='situation-energy-company')
router.register('resquest-types', ResquestTypeViewSet, basename='resquest-type')
router.register('civil-constructions', CivilConstructionViewSet, basename='civil-construction')