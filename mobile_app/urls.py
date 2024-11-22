from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from accounts.views import UserTokenRefreshView
from mobile_app.views import CustomerLoginView


mobile_app_router = DefaultRouter()

# mobile_app_router.get_api_root_view().cls.__name__ = "Mobile App API"
# mobile_app_router.get_api_root_view().cls.__doc__ = "API do Aplicativo Mobile do Cliente da Resolve Energia Solar"


# Exemplo: mobile_app_router.register(r'customers', CustomerViewSet)

schema_view = get_schema_view(
    openapi.Info(
        title="API do App do Cliente",
        default_version='v1',
        description="API do Aplicativo Mobile do Cliente da Resolve Energia Solar",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@resolvenergiasolar.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

app_name = 'mobile_app'
urlpatterns = [
    path('', include(mobile_app_router.urls)),
    path('login/', CustomerLoginView.as_view(), name='customer_login'),
    path('token/refresh/', UserTokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui-mobile_app'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc-mobile_app')
]
