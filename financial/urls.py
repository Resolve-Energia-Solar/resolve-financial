from django.urls import path
from .views import *

app_name = 'financial'
urlpatterns = [
    # Omie API
    path('fornecedores/', SuppliersListView.as_view(), name='suppliers_list'),
    path('categorias/', CategoriesListView.as_view(), name='categories_list'),
    path('criar-fornecedor/', CreateSupplierView.as_view(), name='create_supplier'),
    path('aprovacao-gestor/', ManagerApprovalView.as_view(), name='manager_response'),
    path('solicitacao-de-pagamento/pagar/', PaymentPaidWebhookView.as_view(), name='payment_paid_webhook'),
    # Payment Requests
    path('solicitacao-de-pagamento/criar/', PaymentRequestCreateView.as_view(), name='payment_request_create'),
    path('solicitacao-de-pagamento/', PaymentRequestListView.as_view(), name='payment_request_list'),
    path('solicitacao-de-pagamento/<str:pk>/', PaymentRequestDetailView.as_view(), name='payment_request_detail'),
    path('solicitacao-de-pagamento/<str:pk>/editar/', PaymentRequestUpdateView.as_view(), name='payment_request_update'),
]