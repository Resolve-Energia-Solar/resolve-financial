from accounts.models import Address, User
from inspections.models import *
from rest_framework.serializers import PrimaryKeyRelatedField, SerializerMethodField
from accounts.serializers import AddressSerializer, BaseSerializer, UserSerializer
from resolve_crm.models import Project


class RoofTypeSerializer(BaseSerializer):
      
    class Meta(BaseSerializer.Meta):
        model = RoofType
        fields = '__all__'


class CategorySerializer(BaseSerializer):

    # Para leitura: usar serializador completo
    members = UserSerializer(read_only=True, many=True)

    # Para escrita: usar apenas ID
    members_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='members', many=True)

    class Meta:
        model = Category
        fields = '__all__'


class DeadlineSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Deadline
        fields = '__all__'


class ServiceSerializer(BaseSerializer):  
    
    # Para leitura: usar serializador completo
    category = CategorySerializer(read_only=True, many=False)
    deadline = DeadlineSerializer(read_only=True, many=False)
    
    # Para escrita: usar apenas ID
    category_id = PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True, source='category')
    deadline_id = PrimaryKeyRelatedField(queryset=Deadline.objects.all(), write_only=True, source='deadline')

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


class ScheduleSerializer(BaseSerializer):
    
    # Para leitura: usar serializador completo
    service = ServiceSerializer(read_only=True)
    schedule_agent = UserSerializer(read_only=True)
    address = AddressSerializer(read_only=True)
    project = SerializerMethodField()
    
    # Para escrita: usar apenas ID
    service_id = PrimaryKeyRelatedField(queryset=Service.objects.all(), write_only=True, source='service')
    project_id = PrimaryKeyRelatedField(queryset=Project.objects.all(), write_only=True, source='project')
    schedule_agent_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='schedule_agent')
    address_id = PrimaryKeyRelatedField(queryset=Address.objects.all(), write_only=True, source='address')

    class Meta(BaseSerializer.Meta):
        model = Schedule
        fields = '__all__'

    def get_project(self, obj):
        # problema com o import circular
        from resolve_crm.serializers import ProjectSerializer
        return ProjectSerializer(obj.project).data



class BlockTimeAgentSerializer(BaseSerializer):
    #leitura
    agent = UserSerializer(read_only=True)

    #escrita
    agent_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='agent')

    class Meta(BaseSerializer.Meta):
        model = BlockTimeAgent
        fields = '__all__'

class FreeTimeAgentSerializer(BaseSerializer):
    #leitura
    agent = UserSerializer(read_only=True)

    #escrita
    agent_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='agent')

    class Meta(BaseSerializer.Meta):
        model = FreeTimeAgent
        fields = '__all__'
