from api.urls import router
from financial.views import *


router.register('financiers', FinancierViewSet, basename='financier')
router.register('payments', PaymentViewSet, basename='payment')
router.register('payment-installments', PaymentInstallmentViewSet, basename='payment-installment')
router.register('franchise-installments', FranchiseInstallmentViewSet, basename='franchise-installment')
router.register('financial-records', FinancialRecordViewSet, basename='financial-record')
router.register('bank-details', BankDetailsViewSet, basename='bank-detail')