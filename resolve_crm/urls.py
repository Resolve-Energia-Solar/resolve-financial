from api.urls import router
from resolve_crm.views import *
from resolve_crm.views.sale import OptimizedSaleListViewSet


router.register('origins', OriginViewSet, basename='origin')
router.register('leads', LeadViewSet, basename='lead')
router.register('marketing-campaigns', MarketingCampaignViewSet, basename='marketing-campaign')
router.register('comercial-proposals', ComercialProposalViewSet, basename='comercial-proposal')
router.register('sales', SaleViewSet, basename='sale')
router.register('projects', ProjectViewSet, basename='project')
router.register('contract-submissions', ContractSubmissionViewSet, basename='contract-submission')
router.register('contract-template', ContractTemplateViewSet, basename='contract-template')
router.register('reasons', ReasonViewSet, basename='reason')
router.register('rewards', RewardViewSet, basename='reward')


# API V2
router.register(r'v2/sales', OptimizedSaleListViewSet, basename='optimized-sale-list')
