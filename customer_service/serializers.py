from api.serializers import BaseSerializer
from .models import CustomerService, LostReason


class CustomerServiceSerializer(BaseSerializer):
    class Meta:
        model = CustomerService
        fields = "__all__"


class LostReasonSerializer(BaseSerializer):
    class Meta:
        model = LostReason
        fields = "__all__"