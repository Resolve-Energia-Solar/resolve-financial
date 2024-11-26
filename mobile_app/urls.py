from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.routers import DefaultRouter, APIRootView
from rest_framework import permissions

from accounts.views import UserTokenRefreshView
from mobile_app.views import ContractView, CustomerLoginView, CustomerViewset, FinancialView, SaleViewset


mobile_app_router = DefaultRouter()

class MobileAppAPIRootView(APIRootView):
    """
    API do App do Cliente
    """
    __name__ = "Mobile APP API"

mobile_app_router.APIRootView = MobileAppAPIRootView

mobile_app_schema_view = get_schema_view(
    openapi.Info(
        title="Mobile App API",
        default_version='v1',
        description="API do Aplicativo Mobile",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[path('api/m/', include('mobile_app.urls'))],
)

mobile_app_router.register('customers', CustomerViewset, basename='customer')
mobile_app_router.register('mobile_sales', SaleViewset, basename='mobile_sale')

app_name = 'mobile_app'
urlpatterns = [
    path('login/', CustomerLoginView.as_view(), name='customer_login'),
    path('token/refresh/', UserTokenRefreshView.as_view(), name='customer_token_refresh'),
    path('contracts/<int:project_id>/', ContractView.as_view(), name='contract'),
    path('financial/<int:sale_id>/', FinancialView.as_view(), name='financial'),
    path('', include(mobile_app_router.urls)),
    re_path(r'^swagger/$', mobile_app_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui-mobile_app'),
    re_path(r'^redoc/$', mobile_app_schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc-mobile_app')
]
