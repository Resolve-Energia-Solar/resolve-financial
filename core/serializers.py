from rest_framework.serializers import (
    SerializerMethodField, 
    PrimaryKeyRelatedField, 
    ChoiceField, 
    RelatedField, 
    BooleanField
)

from accounts.models import Branch, User
from accounts.serializers import (
    BranchSerializer, 
    RelatedUserSerializer, 
    ContentTypeSerializer
)
from api.serializers import BaseSerializer
from core.models import *
from resolve_crm.models import Lead, Origin
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
    subtypes_ids = PrimaryKeyRelatedField(queryset=DocumentSubType.objects.all(), many=True, write_only=True, source='subtypes', required=False)
    
    class Meta:
        model = DocumentType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
        

class AttachmentSerializer(BaseSerializer):
    # Para escrita: usar apenas ID
    content_type_id = PrimaryKeyRelatedField(queryset=ContentType.objects.all().order_by('app_label', 'model'), write_only=True, source='content_type')
    document_type_id = PrimaryKeyRelatedField(queryset=DocumentType.objects.all(), write_only=True, source='document_type', required=False)
    document_subtype_id = PrimaryKeyRelatedField(queryset=DocumentSubType.objects.all(), write_only=True, source='document_subtype', required=False)
    
    class Meta:
        model = Attachment
        fields = '__all__'
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['file'] = instance.file.url
        return data
    

class TagSerializer(BaseSerializer):
    content_type_id = PrimaryKeyRelatedField(queryset=ContentType.objects.all().order_by('app_label', 'model'), write_only=True, source='content_type')
    
    class Meta:
        model = Tag
        fields = '__all__'


class CommentSerializer(BaseSerializer):
    author_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='author')
    content_type_id = PrimaryKeyRelatedField(queryset=ContentType.objects.all().order_by('app_label', 'model'), write_only=True, source='content_type')
    
    class Meta:
        model = Comment
        fields = '__all__'


class ColumnNameSerializer(BaseSerializer):
        class Meta:
            model = Column
            fields = ['id', 'name']


class ReadLeadSerializer(BaseSerializer):
    # Para escrita: usar apenas ID
    column_id = PrimaryKeyRelatedField(queryset=Column.objects.all(), write_only=True, source='column')
    origin_id = PrimaryKeyRelatedField(queryset=Origin.objects.all(), write_only=True, source='origin')
    sdr_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='sdr')
    seller_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='seller')

    class Meta:
        model = Lead
        fields = ['id', 'name', 'column', 'column_id', 'contact_email', 'phone', 'seller', 'origin', 'origin_id', 'sdr', 'kwp', 'qualification', 'funnel', 'created_at', 'sdr_id', 'seller_id']


class SimplifiedTaskSerializer(BaseSerializer):
    class Meta:
        model = Task
        fields = ('id', 'title')


class TaskSerializer(BaseSerializer):
    owner_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='owner', required=False)
    column_id = PrimaryKeyRelatedField(queryset=Column.objects.all(), write_only=True, source='column')
    depends_on_ids = PrimaryKeyRelatedField(queryset=Task.objects.all(), many=True, write_only=True, source='depends_on', required=False)

    class Meta:
        model = Task
        fields = '__all__'

class ColumnSerializer(BaseSerializer):
    proposals_value = SerializerMethodField()
    # Para escrita: usar apenas ID
    board_id = PrimaryKeyRelatedField(queryset=Board.objects.all(), write_only=True, source='board')
    column_type = ChoiceField(choices=Column.COLUMN_TYPES, required=False, allow_null=True, allow_blank=True)


    class Meta:
        model = Column
        fields = '__all__'

    def get_proposals_value(self, obj):
        return obj.proposals_value


class BoardSerializer(BaseSerializer):
    # Para escrita: usar apenas IDs
    columns_ids = PrimaryKeyRelatedField(queryset=Column.objects.all(), many=True, write_only=True, source='columns', required=False, allow_null=True)
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, source='branch')

    class Meta:
        model = Board
        fields = '__all__'


class TaskTemplatesSerializer(BaseSerializer):
    depends_on_ids = PrimaryKeyRelatedField(queryset=TaskTemplates.objects.all(), many=True, write_only=True, source='depends_on', required=False)
      
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
