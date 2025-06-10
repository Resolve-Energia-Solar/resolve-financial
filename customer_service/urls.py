from api.urls import router
from .views import CustomerServiceViewSet, LostReasonViewSet, TicketTypeViewSet, TicketViewSet, TicketsSubjectViewSet


router.register('customer-services', CustomerServiceViewSet, basename='customer-service')
router.register('lost-reasons', LostReasonViewSet, basename='lost-reason')
router.register('ticket-types', TicketTypeViewSet, basename='ticket-type')
router.register('tickets', TicketViewSet, basename='ticket')
router.register('tickets-subjects', TicketsSubjectViewSet, basename='tickets-subject')