from django.urls import include, path
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('leads', LeadViewSet, basename='lead')
router.register('tasks', TaskViewSet, basename='task')
router.register('attachments', AttachmentViewSet, basename='attachment')
router.register('squads', SquadViewSet, basename='squad')
router.register('departments', DepartmentViewSet, basename='department')
router.register('branches', BranchViewSet, basename='branch')
router.register('marketing-campaigns', MarketingCampaignViewSet, basename='marketing-campaign')
router.register('addresses', AdressViewSet, basename='address')
router.register('roles', RoleViewSet, basename='role')
router.register('financiers', FinancierViewSet, basename='financier')
router.register('material-types', MaterialTypesViewSet, basename='material-type')
router.register('materials', MaterialsViewSet, basename='material')
router.register('solar-energy-kits', SolarEnergyKitViewSet, basename='solar-energy-kit')
router.register('roof-types', RoofTypeViewSet, basename='roof-type')


app_name = 'api'
urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('', include(router.urls)),
]
