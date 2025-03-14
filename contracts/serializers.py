from api.serializers import BaseSerializer
from .models import SicoobRequest


class SicoobRequestSerializer(BaseSerializer):
    class Meta:
        model = SicoobRequest
        fields = '__all__'
