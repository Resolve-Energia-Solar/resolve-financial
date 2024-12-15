from rest_framework.serializers import SerializerMethodField, PrimaryKeyRelatedField
from accounts.models import Branch, User
from api.serializers import BaseSerializer
from core.models import *
from accounts.serializers import BranchSerializer, RelatedUserSerializer, ContentTypeSerializer
from resolve_crm.models import Lead, Origin


class DocumentSubTypeSerializer(BaseSerializer):
    
    class Meta:
        model = DocumentSubType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentTypeSerializer(BaseSerializer):
    subtypes = DocumentSubTypeSerializer(many=True, read_only=True)
    
    subtypes_ids = PrimaryKeyRelatedField(queryset=DocumentSubType.objects.all(), many=True, write_only=True, source='subtypes', required=False)
    
    class Meta:
        model = DocumentType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
        

class AttachmentSerializer(BaseSerializer):
    
    # Para leitura: usar serializadores completos
    content_type = ContentTypeSerializer(read_only=True)
    document_type = DocumentTypeSerializer(read_only=True)
    document_subtype = DocumentSubTypeSerializer(read_only=True)
    
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


class CommentSerializer(BaseSerializer):
    author = RelatedUserSerializer(read_only=True)
    content_type = ContentTypeSerializer(read_only=True)
    
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
    # Para leitura: usar serializador completo
    column = ColumnNameSerializer(read_only=True)
    origin = SerializerMethodField()
    sdr = RelatedUserSerializer(read_only=True)
    seller = RelatedUserSerializer(read_only=True)

    # Para escrita: usar apenas ID
    column_id = PrimaryKeyRelatedField(queryset=Column.objects.all(), write_only=True, source='column')
    origin_id = PrimaryKeyRelatedField(queryset=Origin.objects.all(), write_only=True, source='origin')
    sdr_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='sdr')
    seller_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='seller')

    class Meta:
        model = Lead
        fields = ['id', 'name', 'column', 'column_id', 'contact_email', 'phone', 'seller', 'origin', 'origin_id', 'sdr', 'kwp', 'qualification', 'funnel', 'created_at', 'sdr_id', 'seller_id']

    def get_origin(self, obj):
        from resolve_crm.serializers import OriginSerializer
        return OriginSerializer(obj.origin).data


class ReadTaskSerializer(BaseSerializer):
    # Para leitura: usar serializador completo
    owner = RelatedUserSerializer(read_only=True)
    
    # Para escrita: usar apenas ID
    owner_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='owner')

    # Campo personalizado para dependências da tarefa
    depends_on = SerializerMethodField()

    class Meta:
        model = Task
        fields = '__all__'

    def get_depends_on(self, obj):
        return TaskSerializer(obj.depends_on, many=True).data


class ColumnSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    leads = ReadLeadSerializer(many=True, read_only=True)
    task = ReadTaskSerializer(many=True, read_only=True)
    proposals_value = SerializerMethodField()

    class Meta:
        model = Column
        fields = '__all__'

    def get_proposals_value(self, obj):
        return obj.proposals_value


class BoardSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    columns = ColumnSerializer(many=True, read_only=True)
    branch = BranchSerializer(read_only=True)

    # Para escrita: usar apenas IDs
    columns_ids = PrimaryKeyRelatedField(queryset=Column.objects.all(), many=True, write_only=True, source='columns')
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, source='branch')

    class Meta:
        model = Board
        fields = '__all__'


class TaskTemplatesSerializer(BaseSerializer):
  
    depends_on = SerializerMethodField()
      
    class Meta:
        model = TaskTemplates
        fields = '__all__'
    
    def get_depends_on(self, obj):
        return TaskTemplatesSerializer(obj.depends_on, many=True).data


class TaskSerializer(BaseSerializer):
    owner = RelatedUserSerializer(read_only=True)
    column = ColumnNameSerializer(read_only=True)
    depends_on = SerializerMethodField()
    project = SerializerMethodField()

    owner_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='owner')
    column_id = PrimaryKeyRelatedField(queryset=Column.objects.all(), write_only=True, source='column')

    class Meta:
        model = Task
        fields = '__all__'
    
    def get_depends_on(self, obj):
        return TaskSerializer(obj.depends_on, many=True).data

    def get_project(self, obj):
        from resolve_crm.serializers import ProjectSerializer
        return ProjectSerializer(obj.project).data
