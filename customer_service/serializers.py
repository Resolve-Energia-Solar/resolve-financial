from api.serializers import BaseSerializer
from .models import CustomerService


class CustomerServiceSerializer(BaseSerializer):
    class Meta:
        model = CustomerService
        fields = "__all__"
