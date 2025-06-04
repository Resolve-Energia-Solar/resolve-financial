from rest_framework.serializers import (
    SerializerMethodField, 
    PrimaryKeyRelatedField, 
    ChoiceField, 
    RelatedField, 
    BooleanField
)
from rest_framework.serializers import ModelSerializer

from accounts.models import User
from api.serializers import BaseSerializer
from core.models import *
from notifications.models import Notification


class SystemConfigSerializer(BaseSerializer):

    class Meta:
        model = SystemConfig
        fields = ['configs']


class DocumentSubTypeSerializer(BaseSerializer):
    
    class Meta:
        model = DocumentSubType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentTypeSerializer(BaseSerializer):
    class Meta:
        model = DocumentType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
        

class AttachmentSerializer(BaseSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['file'] = instance.file.url
        return data
    

class TagSerializer(BaseSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class CommentSerializer(BaseSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class ColumnNameSerializer(BaseSerializer):
        class Meta:
            model = Column
            fields = '__all__'


class SimplifiedTaskSerializer(BaseSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class TaskSerializer(BaseSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class ColumnSerializer(BaseSerializer):
    proposals_value = SerializerMethodField()
    column_type = ChoiceField(choices=Column.COLUMN_TYPES, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Column
        fields = '__all__'

    def get_proposals_value(self, obj):
        total = getattr(obj, 'proposals_total', None)
        return total if total is not None else obj.proposals_value


class BoardSerializer(BaseSerializer):
    class Meta:
        model = Board
        fields = '__all__'


class TaskTemplatesSerializer(BaseSerializer):
    class Meta:
        model = TaskTemplates
        fields = '__all__'

class GenericNotificationRelatedField(RelatedField):
    def to_representation(self, value):
        return str(value)


class NotificationSerializer(BaseSerializer):
    unread = BooleanField()
    target = GenericNotificationRelatedField(read_only=True)
    actor = GenericNotificationRelatedField(read_only=True)
    action_object = GenericNotificationRelatedField(read_only=True)
    timesince = SerializerMethodField()
    
    target_id = PrimaryKeyRelatedField(queryset=ContentType.objects.all().order_by('app_label', 'model'), write_only=True, source='target', required=False)
    actor_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='actor', required=False)
    action_object_id = PrimaryKeyRelatedField(queryset=ContentType.objects.all().order_by('app_label', 'model'), write_only=True, source='action_object', required=False)

    class Meta:
        model = Notification
        fields = '__all__'

    def get_timesince(self, obj):
        return obj.timesince()


class ProcessSerializer(BaseSerializer):
    class Meta:
        model = Process
        fields = '__all__'

    def validate_steps(self, value):
        etapas = value.get("steps", [])
        for etapa in etapas:
            if "id" not in etapa or "nome" not in etapa:
                raise ValidationError("Cada etapa deve conter 'step_id' e 'nome'.")
        return value
    

class StepNameSerializer(BaseSerializer):
    class Meta:
        model = StepName
        fields = ['id', 'name']


class ProcessStepCountSerializer(ModelSerializer):
    
    class Meta:
        model = ProcessStepCount
        fields = ('step', 'total_processes')


class ContentTypeEndpointSerializer(BaseSerializer):
    class Meta:
        model = ContentTypeEndpoint
        fields = ('id', 'endpoint', 'label')