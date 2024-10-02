from rest_framework.serializers import ModelSerializer, SerializerMethodField
from inspections.models import *
from api.serializers.accounts import BaseSerializer


class RoofTypeSerializer(BaseSerializer):
      
      class Meta(BaseSerializer.Meta):
          model = RoofType
          fields = '__all__'