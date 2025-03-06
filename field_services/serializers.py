from accounts.models import Address, User
from core.models import Attachment
from field_services.models import *
from rest_framework.serializers import PrimaryKeyRelatedField, SerializerMethodField
from accounts.serializers import AddressSerializer, BaseSerializer, RelatedUserSerializer
from resolve_crm.models import Lead, Project


class RoofTypeSerializer(BaseSerializer):
      
    class Meta(BaseSerializer.Meta):
        model = RoofType
        fields = '__all__'


class CategorySerializer(BaseSerializer):

    # Para leitura: usar serializador completo
    # members = RelatedUserSerializer(read_only=True, many=True)

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

    class Meta(BaseSerializer.Meta):
        model = Forms
        fields = '__all__'


class ScheduleSerializer(BaseSerializer):
    
    # Para leitura: usar serializador completo
    # service = ServiceSerializer(read_only=True)
    # schedule_agent = RelatedUserSerializer(read_only=True)
    # address = AddressSerializer(read_only=True)
    # project = SerializerMethodField()
    # customer = RelatedUserSerializer(read_only=True)
    service_opinion = SerializerMethodField()
    final_service_opinion = SerializerMethodField()
    attachments = SerializerMethodField()
    
    # Para escrita: usar apenas ID
    attachments_id = PrimaryKeyRelatedField(queryset=Attachment.objects.all(), write_only=True, source='attachments', many=True, required=False)
    service_id = PrimaryKeyRelatedField(queryset=Service.objects.all(), write_only=True, source='service')
    parent_schedules_id = PrimaryKeyRelatedField(queryset=Schedule.objects.all(), write_only=True, source='parent_schedules', many=True, required=False)
    project_id = PrimaryKeyRelatedField(queryset=Project.objects.all(), write_only=True, source='project', required=False, allow_null=True)
    schedule_agent_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='schedule_agent', required=False, allow_null=True)
    address_id = PrimaryKeyRelatedField(queryset=Address.objects.all(), write_only=True, source='address')
    customer_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='customer', required=False, allow_null=True)
    service_opinion_id = PrimaryKeyRelatedField(queryset=ServiceOpinion.objects.all(), write_only=True, source='service_opinion', required=False, allow_null=True)
    final_service_opinion_id = PrimaryKeyRelatedField(queryset=ServiceOpinion.objects.all(), write_only=True, source='final_service_opinion', required=False, allow_null=True)
    leads_ids = PrimaryKeyRelatedField(queryset=Lead.objects.all(), many=True, required=False, write_only=True, source='leads')

    class Meta(BaseSerializer.Meta):
        model = Schedule
        fields = '__all__'
        depth = 1
        
    def get_attachments(self, obj):
        from core.serializers import AttachmentSerializer
        return AttachmentSerializer(obj.attachments, many=True).data
    
    
    def get_service_opinion(self, obj):
        from field_services.serializers import ServiceOpinionSerializer
        return ServiceOpinionSerializer(obj.service_opinion).data if obj.service_opinion else None

    def get_final_service_opinion(self, obj):
        from field_services.serializers import ServiceOpinionSerializer
        return ServiceOpinionSerializer(obj.final_service_opinion).data if obj.final_service_opinion else None




class AnswerSerializer(BaseSerializer):

    # Para leitura: usar serializador completo
    form = FormsSerializer(read_only=True)
    schedule = ScheduleSerializer(read_only=True)

    # Para escrita: usar apenas ID
    form_id = PrimaryKeyRelatedField(queryset=Forms.objects.all(), 
    write_only=True, source='form')
    schedule_id = PrimaryKeyRelatedField(queryset=Schedule.objects.all(), write_only=True, source='schedule')

    class Meta(BaseSerializer.Meta):
        model = Answer
        fields = '__all__'


class BlockTimeAgentSerializer(BaseSerializer):
    #leitura
    agent = RelatedUserSerializer(read_only=True)

    #escrita
    agent_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='agent')

    class Meta(BaseSerializer.Meta):
        model = BlockTimeAgent
        fields = '__all__'

class FreeTimeAgentSerializer(BaseSerializer):
    #leitura
    agent = RelatedUserSerializer(read_only=True)

    #escrita
    agent_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='agent')

    class Meta(BaseSerializer.Meta):
        model = FreeTimeAgent
        fields = '__all__'

class FormFileSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = FormFile
        fields = '__all__'

class ServiceOpinionSerializer(BaseSerializer):
    # Para leitura: usar serializador completo
    service = ServiceSerializer(read_only=True)
    
    # Para escrita: usar apenas ID
    service_id = PrimaryKeyRelatedField(queryset=Service.objects.all(), write_only=True, source='service')
    
    class Meta(BaseSerializer.Meta):
        model = ServiceOpinion
        fields = '__all__'
