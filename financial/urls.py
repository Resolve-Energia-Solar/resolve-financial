from api.urls import router
from financial.views import *


router.register('financiers', FinancierViewSet, basename='financier')
router.register('payments', PaymentViewSet, basename='payment')
router.register('payment-installments', PaymentInstallmentViewSet, basename='payment-installment')
