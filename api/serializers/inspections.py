from rest_framework.serializers import ModelSerializer, SerializerMethodField, PrimaryKeyRelatedField
from accounts.models import Squad
from inspections.models import *
from api.serializers.accounts import BaseSerializer, SquadSerializer


class RoofTypeSerializer(BaseSerializer):
      
    class Meta(BaseSerializer.Meta):
        model = RoofType
        fields = '__all__'

class CategorySerializer(BaseSerializer): 
    # Para leitura: usar serializador completo
    squads = SquadSerializer(read_only=True, many=True)
    # Para escrita: usar apenas ID
    squads_id = PrimaryKeyRelatedField(queryset=Squad.objects.all(), write_only=True, source='squads', many=True)

    class Meta:
        model = Category
        fields = '__all__'

class ServiceSerializer(BaseSerializer):  
    # Para leitura: usar serializador completo
    category = CategorySerializer(read_only=True, many=False)
    # Para escrita: usar apenas ID
    category_id = PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True, source='category')

    class Meta(BaseSerializer.Meta):
        model = Service
        fields = '__all__'

class FormsSerializer(BaseSerializer):
    # Para leitura: usar serializador completo
    service = ServiceSerializer(read_only=True)
    # Para escrita: usar apenas ID
    service_id = PrimaryKeyRelatedField(queryset=Service.objects.all(), write_only=True, source='service')

    class Meta(BaseSerializer.Meta):
        model = Forms
        fields = '__all__'

class AnswerSerializer(BaseSerializer):
    # Para leitura: usar serializador completo
    form = FormsSerializer(read_only=True)
    # Para escrita: usar apenas ID
    form_id = PrimaryKeyRelatedField(queryset=Forms.objects.all(), write_only=True, source='form')

    class Meta(BaseSerializer.Meta):
        model = Answer
        fields = '__all__'