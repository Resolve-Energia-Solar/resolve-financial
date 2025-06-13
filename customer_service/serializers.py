from api.serializers import BaseSerializer
from .models import CustomerService, LostReason, Ticket, TicketType, TicketsSubject
from rest_framework.serializers import SerializerMethodField


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
    duration = SerializerMethodField()

    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = (
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

    def get_duration(self, obj):
        return str(obj.duration)

    def create(self, validated_data):
        current_user = validated_data.pop("current_user", None)
        ticket = Ticket(**validated_data)
        ticket.save(current_user=current_user)
        return ticket


class TicketsSubjectSerializer(BaseSerializer):
    class Meta:
        model = TicketsSubject
        fields = "__all__"
