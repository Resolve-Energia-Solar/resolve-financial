from api.urls import router
from .views import SicoobRequestViewSet


router.register('sicoob-requests', SicoobRequestViewSet, basename='sicoob-request')