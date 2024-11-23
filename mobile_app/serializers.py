from accounts.models import User
from api.serializers import BaseSerializer
from accounts.serializers import PhoneNumberSerializer


class CustomerSerializer(BaseSerializer):
    phone_numbers = PhoneNumberSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'person_type', 'complete_name', 'email', 'birth_date', 'first_document', 'profile_picture', 'phone_numbers']
