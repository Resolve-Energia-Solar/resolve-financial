from django.urls import path, re_path, include


from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.routers import DefaultRouter, APIRootView
from rest_framework import permissions

from accounts.views import PasswordResetConfirmView, PasswordResetRequestView, UserLoginView, UserTokenRefreshView
from contracts.views import InformacaoFaturaAPIView, ReciveContractInfomation
from core.views import CreateTasksFromSaleView, HistoryView, SystemConfigView
from customer_service.views import tickets_por_departamento
from engineering.views import ProjectMaterialsCSVUploadAPIView
from financial.views import FinancialRecordApprovalView, OmieIntegrationView, UpdateFinancialRecordPaymentStatus, SendFinancialRecordsToOmieView
from resolve_crm.views import GenerateContractView, GenerateCustomContract, GeneratePreSaleView, GenerateSalesProjectsView, ValidateContractView
from .views import GanttView, StatusView
from resolve_crm.views import save_all_sales_func
from resolve_crm.views import list_sales_func


router = DefaultRouter()

class ErpApiRootView(APIRootView):
    """
    API do ERP da Resolve Energia Solar
    """

router.APIRootView = ErpApiRootView

import accounts.urls
import core.urls
import contracts.urls
import engineering.urls
import financial.urls
import field_services.urls
import logistics.urls
import resolve_crm.urls
import customer_service.urls

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
    path('', include(core.urls)),
    path('', include(contracts.urls)),
    path('login/', UserLoginView.as_view(), name='login'),
    path('token/refresh/', UserTokenRefreshView.as_view(), name='token_refresh'),
    path('generate-pre-sale/', GeneratePreSaleView.as_view(), name='generate_pre_sale'),
    path('system-config/', SystemConfigView.as_view(), name='system-config'),
    path('history/', HistoryView.as_view(), name='history'),
    path('fatura/', InformacaoFaturaAPIView.as_view(), name='invoice_information'),
    path('generate-projects/', GenerateSalesProjectsView.as_view(), name='generate_projects'),
    path('create-tasks/', CreateTasksFromSaleView.as_view(), name='create_tasks'),
    path('projects/insert-materials/', ProjectMaterialsCSVUploadAPIView.as_view(), name='insert_materials'),
    path('', include(router.urls)),
    re_path(r'^swagger/$', api_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', api_schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('validate-contract/', ValidateContractView.as_view(), name='validate_contract'),
    path('gantt/', GanttView.as_view(), name='gantt'),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path('generate-contract/', GenerateContractView.as_view(), name='generate_contract'),
    path('generate-custom-contract/', GenerateCustomContract.as_view(), name='generate_custom_contract'),
    path('recive-contract-infomation/', ReciveContractInfomation.as_view(), name='recive_contract_infomation'),
    path('status/', StatusView.as_view(), name='status'),
    path('financial/omie/', OmieIntegrationView.as_view(), name='omie_integration'),
    path('financial/approve-financial-record/', FinancialRecordApprovalView.as_view(), name='approve_financial_record'),
    path('financial/omie/send-financial-records/', SendFinancialRecordsToOmieView.as_view() , name='send_financial_records_to_omie'),
    path('financial/omie/update-financial-record-payment-status/', UpdateFinancialRecordPaymentStatus.as_view(), name='update_financial_record_payment_status'),
    path('save-sales/', save_all_sales_func , name='save_sales'),    
    path('list-sale/', list_sales_func , name='simple_serializer'),
    path("tickets-por-departamento/", tickets_por_departamento, name="tickets_por_departamento"),

]
