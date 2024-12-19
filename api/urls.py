from django.urls import path, re_path, include


from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.routers import DefaultRouter, APIRootView
from rest_framework import permissions

from accounts.views import UserLoginView, UserTokenRefreshView
from contracts.views import InformacaoFaturaAPIView
from core.views import HistoryView
from resolve_crm.views import GeneratePreSaleView, GenerateSalesProjectsView
from .views import ContratoView, GanttView


router = DefaultRouter()

class ErpApiRootView(APIRootView):
    """
    API do ERP da Resolve Energia Solar
    """

router.APIRootView = ErpApiRootView

import accounts.urls
import core.urls
import engineering.urls
import financial.urls
import inspections.urls
import logistics.urls
import resolve_crm.urls

api_schema_view = get_schema_view(
    openapi.Info(
        title="ERP API",
        default_version='v1',
        description="API do ERP",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[path('api/', include('api.urls'))],
)

app_name = 'api'
urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('token/refresh/', UserTokenRefreshView.as_view(), name='token_refresh'),
    path('generate-pre-sale/', GeneratePreSaleView.as_view(), name='generate_pre_sale'),
    path('history/', HistoryView.as_view(), name='history'),
    path('fatura/', InformacaoFaturaAPIView.as_view(), name='invoice_information'),
    path('generate-projects/', GenerateSalesProjectsView.as_view(), name='generate_projects'), 
    path('', include(router.urls)),
    re_path(r'^swagger/$', api_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', api_schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('send-contract/', ContratoView.as_view(), name='send_contract'),  
    path('gantt/', GanttView.as_view(), name='gantt'),
]
