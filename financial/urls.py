from django.urls import path
from .views import *

app_name = 'financial'
urlpatterns = [
    # Payment Requests
    path('solicitacao-de-pagamento/criar/', PaymentRequestCreateView.as_view(), name='payment_request_create'),
    path('solicitacao-de-pagamento/', PaymentRequestListView.as_view(), name='payment_request_list'),
    path('solicitacao-de-pagamento/<int:pk>/', PaymentRequestDetailView.as_view(), name='payment_request_detail'),
    path('solicitacao-de-pagamento/<int:pk>/editar/', PaymentRequestUpdateView.as_view(), name='payment_request_update'),
]