from rest_framework.serializers import ModelSerializer, SerializerMethodField, PrimaryKeyRelatedField
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from core.models import TaskTemplates
from accounts.models import *


class BaseSerializer(ModelSerializer):
    
    class Meta:
        model = None
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'is_deleted' in self.fields:
            self.fields.pop('is_deleted')


class DepartmentSerializer(BaseSerializer):
    class Meta:
        model = Department
        exclude = ['is_deleted']
        
        
class RoleSerializer(BaseSerializer):
    class Meta:
        model = Role
        exclude = ['is_deleted']
        
        
class RelatedUserSerializer(BaseSerializer):
        
    class Meta:
        model = User
        fields = ['id', 'complete_name', 'email', 'phone']


class AddressSerializer(BaseSerializer):
    
    class Meta:
        model = Address
        exclude = ['is_deleted']


class BranchSerializer(ModelSerializer):
    # Para leitura: usar serializadores completos
    owners = RelatedUserSerializer(many=True, read_only=True)
    address = AddressSerializer(read_only=True)

    # Para escrita: usar apenas IDs
    owners_ids = PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, write_only=True, source='owners')
    address_id = PrimaryKeyRelatedField(queryset=Address.objects.all(), write_only=True, source='address')

    class Meta:
        model = Branch
        exclude = ['is_deleted']


class UserTypeSerializer(BaseSerializer):
        
        class Meta:
            model = UserType
            fields = '__all__'


class ContentTypeSerializer(BaseSerializer):
        
        class Meta:
            model = ContentType
            fields = '__all__'


class PermissionSerializer(ModelSerializer):
    # Para leitura: usar serializador completo
    content_type = ContentTypeSerializer(read_only=True)

    # Para escrita: usar apenas ID
    content_type_id = PrimaryKeyRelatedField(queryset=ContentType.objects.all(), write_only=True, source='content_type')

    class Meta:
        model = Permission
        fields = '__all__'


class GroupSerializer(ModelSerializer):
    # Para leitura: usar serializador completo
    permissions = PermissionSerializer(many=True, read_only=True)

    # Para escrita: usar apenas IDs
    permissions_ids = PrimaryKeyRelatedField(queryset=Permission.objects.all(), many=True, write_only=True, source='permissions')

    class Meta:
        model = Group
        fields = '__all__'


class UserSerializer(ModelSerializer):
    # Para leitura: usar serializadores completos
    branch = BranchSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    role = RoleSerializer(read_only=True)
    user_manager = RelatedUserSerializer(read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)
    user_types = UserTypeSerializer(many=True, read_only=True)
    groups = GroupSerializer(many=True, read_only=True)

    # Para escrita: usar apenas IDs
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, source='branch')
    department_id = PrimaryKeyRelatedField(queryset=Department.objects.all(), write_only=True, source='department')
    role_id = PrimaryKeyRelatedField(queryset=Role.objects.all(), write_only=True, source='role')
    user_manager_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='user_manager')
    addresses_ids = PrimaryKeyRelatedField(queryset=Address.objects.all(), many=True, write_only=True, source='addresses')
    user_types_ids = PrimaryKeyRelatedField(queryset=UserType.objects.all(), many=True, write_only=True, source='user_types')
    groups_ids = PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True, write_only=True, source='groups')

    user_permissions = SerializerMethodField()
    distance = SerializerMethodField()
    daily_schedules_count = SerializerMethodField()

    class Meta:
        model = User
        exclude = ['password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request')
        if request and not request.query_params.get('latitude') and not request.query_params.get('longitude'):
            self.fields.pop('distance', None)
            self.fields.pop('daily_schedules_count', None)

    def get_user_permissions(self, obj):
        return obj.get_all_permissions()
    
    def get_distance(self, obj):
        return obj.distance
    
    def get_daily_schedules_count(self, obj):
        return obj.daily_schedules_count


class TaskTemplatesSerializer(BaseSerializer):
  
    depends_on = SerializerMethodField()
      
    class Meta:
        model = TaskTemplates
        fields = '__all__'
    
    def get_depends_on(self, obj):
        return TaskTemplatesSerializer(obj.depends_on, many=True).data


class SquadSerializer(ModelSerializer):
    # Para leitura: usar serializadores completos
    branch = BranchSerializer(read_only=True)
    manager = RelatedUserSerializer(read_only=True)
    members = RelatedUserSerializer(many=True, read_only=True)

    # Para escrita: usar apenas IDs
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, source='branch')
    manager_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='manager')
    members_ids = PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, write_only=True, source='members')

    boards = SerializerMethodField()

    class Meta:
        model = Squad
        fields = '__all__'

    def get_boards(self, obj):
        from api.serializers.core import BoardSerializer
        return BoardSerializer(obj.boards, many=True).data
