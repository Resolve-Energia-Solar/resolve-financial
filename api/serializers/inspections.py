from rest_framework.serializers import ModelSerializer, SerializerMethodField, PrimaryKeyRelatedField
from accounts.models import Squad
from inspections.models import *
from api.serializers.accounts import BaseSerializer, SquadSerializer


class RoofTypeSerializer(BaseSerializer):
      
    class Meta(BaseSerializer.Meta):
        model = RoofType
        fields = '__all__'

class SquadSimpleSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Squad
        fields = ['id', 'name']

class CategorySerializer(BaseSerializer): 
    # leitura de squads
    squads = SquadSimpleSerializer(many=True, read_only=True)

    # escrita de squads por id
    squads = PrimaryKeyRelatedField(queryset=Squad.objects.all(), many=True, required=False)

    class Meta:
        model = Category
        fields = '__all__'

class ServiceSerializer(BaseSerializer):  
    category = CategorySerializer(read_only=True)

    class Meta(BaseSerializer.Meta):
        model = Service
        fields = '__all__'

class FormsSerializer(BaseSerializer):
    service = ServiceSerializer(read_only=True)

    class Meta(BaseSerializer.Meta):
        model = Forms
        fields = '__all__'

class AnswerSerializer(BaseSerializer):
    form = FormsSerializer(read_only=True)

    class Meta(BaseSerializer.Meta):
        model = Answer
        fields = '__all__'