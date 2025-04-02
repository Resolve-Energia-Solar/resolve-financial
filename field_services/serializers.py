from field_services.models import *
from accounts.serializers import BaseSerializer


class RoofTypeSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = RoofType
        fields = '__all__'


class CategorySerializer(BaseSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class DeadlineSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Deadline
        fields = '__all__'


class ServiceSerializer(BaseSerializer):  
    class Meta(BaseSerializer.Meta):
        model = Service
        fields = '__all__'


class FormsSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Forms
        fields = '__all__'

class ScheduleSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Schedule
        fields = '__all__'

class AnswerSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Answer
        fields = '__all__'


class BlockTimeAgentSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = BlockTimeAgent
        fields = '__all__'

class FreeTimeAgentSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = FreeTimeAgent
        fields = '__all__'

class FormFileSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = FormFile
        fields = '__all__'

class ServiceOpinionSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = ServiceOpinion
        fields = '__all__'


class RouteSerializer(BaseSerializer):
    class Meta:
        model = Route
        fields = '__all__'