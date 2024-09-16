from rest_framework.serializers import ModelSerializer, SerializerMethodField
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from accounts.models import *
    
        
class DepartmentSerializer(ModelSerializer):
    class Meta:
        model = Department
        exclude = ['is_deleted']
        
        
class RoleSerializer(ModelSerializer):
    class Meta:
        model = Role
        exclude = ['is_deleted']
        
        
class RelatedUserSerializer(ModelSerializer):
        
    class Meta:
        model = User
        fields = ['id', 'complete_name', 'email', 'phone']


class AddressSerializer(ModelSerializer):
    
    class Meta:
        model = Address
        exclude = ['is_deleted']


class BranchSerializer(ModelSerializer):

    owners = RelatedUserSerializer(many=True)
    address = AddressSerializer()

    class Meta:
        model = Branch
        exclude = ['is_deleted']


class UserTypeSerializer(ModelSerializer):
        
        class Meta:
            model = UserType
            fields = '__all__'


class ContentTypeSerializer(ModelSerializer):
        
        class Meta:
            model = ContentType
            fields = '__all__'


class PermissionSerializer(ModelSerializer):
    
    content_type = ContentTypeSerializer()
    
    class Meta:
        model = Permission
        fields = '__all__'


class GroupSerializer(ModelSerializer):
    
    permissions = PermissionSerializer(many=True)
    
    class Meta:
        model = Group
        fields = '__all__'


class UserSerializer(ModelSerializer):
    
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
