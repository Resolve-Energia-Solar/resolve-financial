from django.urls import path, re_path, include


from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from accounts.views import UserLoginView, UserTokenRefreshView
from contracts.views import InformacaoFaturaAPIView
from core.views import HistoryView
from resolve_crm.views import GeneratePreSaleView, GenerateSalesProjectsView


router = DefaultRouter()

router.get_api_root_view().cls.__name__ = "E.R.P. Resolve API"
router.get_api_root_view().cls.__doc__ = "API do ERP da Resolve Energia Solar"

import accounts.urls
import core.urls
import engineering.urls
import financial.urls
import inspections.urls
import logistics.urls
import resolve_crm.urls

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
    path('generate-pre-sale/', GeneratePreSaleView.as_view(), name='generate_pre_sale'),
    path('history/', HistoryView.as_view(), name='history'),
    path('fatura/', InformacaoFaturaAPIView.as_view(), name='invoice_information'),
    path('generate-projects/', GenerateSalesProjectsView.as_view(), name='generate_projects'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
