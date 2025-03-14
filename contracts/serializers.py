from api.serializers import BaseSerializer
from .models import SicoobRequest
from rest_framework.exceptions import ValidationError


class SicoobRequestSerializer(BaseSerializer):
    class Meta:
        model = SicoobRequest
        fields = '__all__'

    def validate(self, data):
        customer = data.get('customer')
        if customer and getattr(customer, 'person_type', None) == 'PJ' and not data.get('managing_partner'):
            raise ValidationError({
                'details': 'Sócio administrador é obrigatório para solicitações cujo cliente é pessoa jurídica.'
            })
        return data
