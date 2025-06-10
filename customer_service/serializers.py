from api.serializers import BaseSerializer
from .models import CustomerService, LostReason, Ticket, TicketType, TicketsSubject


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
        read_only_fields = (
            "responsible",
            "responsible_department",
            "deadline",
            "answered_at",
            "answered_by",
            "resolved_at",
            "resolved_by",
            "closed_at",
            "closed_by",
            "conclusion_date",
        )

    def create(self, validated_data):
        current_user = validated_data.pop("current_user", None)
        ticket = Ticket(**validated_data)
        ticket.save(current_user=current_user)
        return ticket


class TicketsSubjectSerializer(BaseSerializer):
    class Meta:
        model = TicketsSubject
        fields = "__all__"
