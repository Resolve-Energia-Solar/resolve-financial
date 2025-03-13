from api.serializers import BaseSerializer
from .models import SicoobRequest
from rest_framework import serializers


class SicoobRequestSerializer(BaseSerializer):
    class Meta:
        model = SicoobRequest
        fields = '__all__'
