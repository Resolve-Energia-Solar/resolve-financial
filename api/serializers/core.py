from rest_framework.serializers import SerializerMethodField, PrimaryKeyRelatedField
from accounts.models import Branch, User
from api.serializers.accounts import BaseSerializer
from core.models import *
from .accounts import BranchSerializer, RelatedUserSerializer, ContentTypeSerializer
from resolve_crm.models import Lead, Origin


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
        from api.serializers.resolve_crm import OriginSerializer
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

    class Meta:
        model = Column
        fields = '__all__'


class BoardSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    columns = ColumnSerializer(many=True, read_only=True)
    branch = BranchSerializer(read_only=True)

    # Para escrita: usar apenas IDs
    columns_ids = PrimaryKeyRelatedField(queryset=Column.objects.all(), many=True, write_only=True, source='columns')
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, source='branch')

    class Meta:
        model = Board
        fields = ['id', 'title', 'description', 'columns', 'branch', 'columns_ids', 'branch_id']
    

class TaskSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    owner = RelatedUserSerializer(read_only=True)
    board = BoardSerializer(read_only=True)
    content_type = ContentTypeSerializer(read_only=True)
    lead = ReadLeadSerializer(read_only=True)
    depends_on = SerializerMethodField()
    project = SerializerMethodField()

    # Para escrita: usar apenas IDs
    owner_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='owner')
    board_id = PrimaryKeyRelatedField(queryset=Board.objects.all(), write_only=True, source='board')
    content_type_id = PrimaryKeyRelatedField(queryset=ContentType.objects.all(), write_only=True, source='content_type')
    lead_id = PrimaryKeyRelatedField(queryset=Lead.objects.all(), write_only=True, source='lead')

    class Meta:
        model = Task
        fields = '__all__'

    def get_depends_on(self, obj):
        return TaskSerializer(obj.depends_on, many=True).data

    def get_project(self, obj):
        from .resolve_crm import ProjectSerializer
        return ProjectSerializer(obj.project).data
