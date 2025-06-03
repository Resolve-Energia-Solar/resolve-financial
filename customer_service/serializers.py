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
        fields = [
            "id",
            "project",
            "subject",
            "description",
            "ticket_type",
            "priority",
            "responsible_user",
            "conclusion_date",
            "status",
            "responsible",
            "responsible_department",
            "deadline",
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "responsible",           
            "responsible_department",
            "deadline",
            "answered_at", "answered_by",
            "resolved_at", "resolved_by",
            "closed_at", "closed_by",
            "conclusion_date",
        )