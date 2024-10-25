from django.urls import path, re_path, include
from .views import *
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions


router = DefaultRouter()

router.get_api_root_view().cls.__name__ = "E.R.P. Resolve API"
router.get_api_root_view().cls.__doc__ = "API do ERP da Resolve Energia Solar"

router.register('users', UserViewSet, basename='user')
router.register('leads', LeadViewSet, basename='lead')
router.register('lead-tasks', TaskViewSet, basename='lead-task')
router.register('attachments', AttachmentViewSet, basename='attachment')
router.register('squads', SquadViewSet, basename='squad')
router.register('departments', DepartmentViewSet, basename='department')
router.register('branches', BranchViewSet, basename='branch')
router.register('marketing-campaigns', MarketingCampaignViewSet, basename='marketing-campaign')
router.register('addresses', AddressViewSet, basename='address')
router.register('roles', RoleViewSet, basename='role')
router.register('content-types', ContentTypeViewSet, basename='content-type')
router.register('permissions', PermissionViewSet, basename='permission')
router.register('groups', GroupViewSet, basename='group')
router.register('material-types', MaterialTypesViewSet, basename='material-type')
router.register('materials', MaterialsViewSet, basename='material')
router.register('solar-energy-kits', SolarEnergyKitViewSet, basename='solar-energy-kit')
router.register('roof-types', RoofTypeViewSet, basename='roof-type')
router.register('energy-companies', EnergyCompanyViewSet, basename='energycompany')
router.register('requests-energy-companies', RequestsEnergyCompanyViewSet, basename='requestsenergycompany')
router.register('circuit-breakers', CircuitBreakerViewSet, basename='circuitbreaker')
router.register('tasks', TaskViewSet, basename='task')
router.register('task-templates', TaskTemplatesViewSet, basename='task-template')
router.register('boards', BoardViewSet, basename='board')
router.register('columns', ColumnViewSet, basename='column')
router.register('units', UnitsViewSet, basename='unit')
router.register('comercial-proposals', ComercialProposalViewSet, basename='comercial-proposal')
router.register('sales', SaleViewSet, basename='sale')
router.register('projects', ProjectViewSet, basename='project')
router.register('financiers', FinancierViewSet, basename='financier')
router.register('payments', PaymentViewSet, basename='payment')
router.register('payment-installments', PaymentInstallmentViewSet, basename='payment-installment')

schema_view = get_schema_view(
    openapi.Info(
        title="ERP Resolve API",
        default_version='v1',
        description="API do ERP da Resolve Energia Solar",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@resolvenergiasolar.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

app_name = 'api'
urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('token/refresh/', UserTokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
    path('history/', HistoryView.as_view(), name='history'),
    path('fatura/', InformacaoFaturaAPIView.as_view(), name='invoice_information'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
