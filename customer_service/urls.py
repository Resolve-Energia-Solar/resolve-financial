from api.urls import router
from .views import CustomerServiceViewSet


router.register('customer-services', CustomerServiceViewSet, basename='customer-service')