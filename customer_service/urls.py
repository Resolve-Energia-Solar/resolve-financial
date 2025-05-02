from api.urls import router
from .views import CustomerServiceViewSet, LostReasonViewSet


router.register('customer-services', CustomerServiceViewSet, basename='customer-service')
router.register('lost-reasons', LostReasonViewSet, basename='lost-reason')