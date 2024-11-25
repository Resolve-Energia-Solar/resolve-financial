from accounts.models import User
from api.serializers import BaseSerializer
from accounts.serializers import PhoneNumberSerializer, RelatedUserSerializer
from resolve_crm.models import Sale
from rest_framework.serializers import Serializer


class CustomerSerializer(BaseSerializer):

    phone_numbers = PhoneNumberSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'person_type', 'complete_name', 'email', 'birth_date', 'first_document', 'profile_picture', 'phone_numbers']


class MobileSaleSerializer(BaseSerializer):

    customer = RelatedUserSerializer(read_only=True)
    seller = RelatedUserSerializer(read_only=True)
    sales_supervisor = RelatedUserSerializer(read_only=True)
    sales_manager = RelatedUserSerializer(read_only=True)
    
    class Meta:
        model = Sale
        fields = ['id', 'contract_number', 'customer', 'seller', 'sales_supervisor', 'sales_manager', 'status', 'created_at', 'total_value', 'signature_date', 'branch', 'is_pre_sale']
