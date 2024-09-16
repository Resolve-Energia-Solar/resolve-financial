from django.urls import include, path
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.get_api_root_view().cls.__name__ = "E.R.P. Resolve API"
router.get_api_root_view().cls.__doc__ = "API do ERP da Resolve Energia Solar"

router.register('users', UserViewSet, basename='user')
router.register('leads', LeadViewSet, basename='lead')
router.register('tasks', TaskViewSet, basename='task')
router.register('attachments', AttachmentViewSet, basename='attachment')
router.register('squads', SquadViewSet, basename='squad')
router.register('departments', DepartmentViewSet, basename='department')
router.register('branches', BranchViewSet, basename='branch')
router.register('marketing-campaigns', MarketingCampaignViewSet, basename='marketing-campaign')
router.register('addresses', AddressViewSet, basename='address')
router.register('roles', RoleViewSet, basename='role')
router.register('permissions', PermissionViewSet, basename='permission')
router.register('groups', GroupViewSet, basename='group')
router.register('financiers', FinancierViewSet, basename='financier')
router.register('material-types', MaterialTypesViewSet, basename='material-type')
router.register('materials', MaterialsViewSet, basename='material')
router.register('solar-energy-kits', SolarEnergyKitViewSet, basename='solar-energy-kit')
router.register('roof-types', RoofTypeViewSet, basename='roof-type')

router.register('energy-companies', EnergyCompanyViewSet, basename='energycompany')
router.register('requests-energy-companies', RequestsEnergyCompanyViewSet, basename='requestsenergycompany')
router.register('circuit-breakers', CircuitBreakerViewSet, basename='circuitbreaker')

app_name = 'api'
urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('', include(router.urls)),
]
