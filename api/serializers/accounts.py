from rest_framework.serializers import ModelSerializer, SerializerMethodField
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
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


class BranchSerializer(BaseSerializer):

    owners = RelatedUserSerializer(many=True)
    address = AddressSerializer()

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


class PermissionSerializer(BaseSerializer):
    
    content_type = ContentTypeSerializer()
    
    class Meta:
        model = Permission
        fields = '__all__'


class GroupSerializer(BaseSerializer):
    
    permissions = PermissionSerializer(many=True)
    
    class Meta:
        model = Group
        fields = '__all__'


class UserSerializer(BaseSerializer):
    
    branch = BranchSerializer()
    department = DepartmentSerializer()
    role = RoleSerializer()
    user_manager = RelatedUserSerializer()
    addresses = AddressSerializer(many=True)
    user_permissions = SerializerMethodField()
    user_types = UserTypeSerializer(many=True)
    groups = GroupSerializer(many=True)
    
    class Meta:
        model = User
        fields = '__all__'

    def get_user_permissions(self, obj):
        return obj.get_all_permissions()

class SquadSerializer(BaseSerializer):
    
    branch = BranchSerializer()
    manager = RelatedUserSerializer()
    members = RelatedUserSerializer(many=True)
    #analisar como mandará os boards
    
    
    class Meta:
        model = Squad
        exclude = ['is_deleted']
        
