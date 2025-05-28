from api.serializers import BaseSerializer
from .models import CustomerService, LostReason, Ticket, TicketType


class CustomerServiceSerializer(BaseSerializer):
    class Meta:
        model = CustomerService
        fields = "__all__"


class LostReasonSerializer(BaseSerializer):
    class Meta:
        model = LostReason
        fields = "__all__"
        
    
class TicketTypeSerializer(BaseSerializer):
    class Meta:
        model = TicketType
        fields = "__all__"


class TicketSerializer(BaseSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"