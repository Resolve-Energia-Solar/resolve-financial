from rest_framework.serializers import SerializerMethodField, PrimaryKeyRelatedField
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from api.serializers import BaseSerializer
from accounts.models import *


class DepartmentSerializer(BaseSerializer):
    class Meta:
        model = Department
        exclude = ['is_deleted']
        
        
class RoleSerializer(BaseSerializer):
    class Meta:
        model = Role
        exclude = ['is_deleted']


class PhoneNumberSerializer(BaseSerializer):
    user = SerializerMethodField(read_only=True)  # Apenas leitura
    user_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='user')  # Apenas escrita

    class Meta:
        model = PhoneNumber
        fields = '__all__'

    def create(self, validated_data):
        # Extraia o usuário dos dados validados
        user = validated_data.pop('user', None)
        
        # Crie o objeto de telefone
        phone_number = PhoneNumber.objects.create(user=user, **validated_data)
        return phone_number

    def get_user(self, obj):
        # Retorna informações básicas do usuário
        if obj.user:
            return {
                "id": obj.user.id,
                "complete_name": obj.user.complete_name,
            }
        return None


class RelatedUserSerializer(BaseSerializer):
    phone_numbers = PhoneNumberSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'complete_name', 'birth_date', 'first_document', 'email', 'phone_numbers']


class AddressSerializer(BaseSerializer):
    user_id = PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, required=False,
    )

    class Meta:
        model = Address
        fields = '__all__'

    def create(self, validated_data):
        if 'user_id' in validated_data:
            # Obter o ID do usuário a partir dos dados validados
            user = validated_data.pop('user_id')
            # Criar o endereço
            address = Address.objects.create(**validated_data)
            # Adicionar o endereço ao campo 'addresses' do usuário
            user.addresses.add(address)
            return address
        return Address.objects.create(**validated_data)


class BranchSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    owners = RelatedUserSerializer(many=True, read_only=True)
    address = AddressSerializer(read_only=True)

    # Para escrita: usar apenas IDs
    owners_ids = PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, write_only=True, source='owners')
    address_id = PrimaryKeyRelatedField(queryset=Address.objects.all(), write_only=True, source='address')

    class Meta:
        model = Branch
        exclude = ['is_deleted']


class ContentTypeSerializer(BaseSerializer):
        
        class Meta:
            model = ContentType
            fields = '__all__'


class PermissionSerializer(BaseSerializer):
    # Para leitura: usar serializador completo
    content_type = ContentTypeSerializer(read_only=True)

    # Para escrita: usar apenas ID
    content_type_id = PrimaryKeyRelatedField(queryset=ContentType.objects.all(), write_only=True, source='content_type')

    class Meta:
        model = Permission
        fields = '__all__'


class GroupSerializer(BaseSerializer):
    # Para leitura: usar serializador completo
    permissions = PermissionSerializer(many=True, read_only=True)

    # Para escrita: usar apenas IDs
    permissions_ids = PrimaryKeyRelatedField(queryset=Permission.objects.all(), many=True, write_only=True, source='permissions')

    class Meta:
        model = Group
        fields = '__all__'
        

class UserTypeSerializer(BaseSerializer):
        
        class Meta:
            model = UserType
            fields = '__all__'


class UserSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    addresses = AddressSerializer(many=True, read_only=True)
    user_types = UserTypeSerializer(many=True, read_only=True)
    groups = GroupSerializer(many=True, read_only=True)
    phone_numbers = PhoneNumberSerializer(many=True, read_only=True)

    # Para escrita: usar apenas IDs
    addresses_ids = PrimaryKeyRelatedField(queryset=Address.objects.all(), many=True, write_only=True, source='addresses', allow_null=True)
    user_types_ids = PrimaryKeyRelatedField(queryset=UserType.objects.all(), many=True, write_only=True, source='user_types', allow_null=True)
    groups_ids = PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True, write_only=True, source='groups', allow_null=True, required=False)
    phone_numbers_ids = PrimaryKeyRelatedField(queryset=PhoneNumber.objects.all(), many=True, write_only=True, source='phone_numbers', allow_null=True)

    user_permissions = SerializerMethodField()
    distance = SerializerMethodField()
    daily_schedules_count = SerializerMethodField()

    class Meta:
        model = User
        exclude = ['password']
        
    def get_user_permissions(self, obj):
        return obj.get_all_permissions()
    
    def get_distance(self, obj):
        return getattr(obj, 'distance', None)
    
    def get_daily_schedules_count(self, obj):
        return getattr(obj, 'daily_schedules_count', None)
    

class EmployeeSerializer(BaseSerializer):
    user = UserSerializer()

    class Meta:
        model = Employee
        fields = ['user', 'contract_type', 'branch', 'department', 'role', 'user_manager', 'hire_date']
        
    def create(self, validated_data):
        # Extrair dados do usuário
        user_data = validated_data.pop('user')
        addresses = user_data.pop('addresses', [])
        user_types = user_data.pop('user_types', [])
        groups = user_data.pop('groups', [])
        
        # Criar o usuário primeiro
        user = User.objects.create(**user_data)
        
        # Atribuir relações many-to-many após a criação do usuário
        if addresses:
            user.addresses.set(addresses)
        if user_types:
            user.user_types.set(user_types)
        if groups:
            user.groups.set(groups)
        
        # Criar o empregado associado
        employee = Employee.objects.create(user=user, **validated_data)
        return employee


    def update(self, instance, validated_data):
        user_data = validated_data.pop('user')
        user = instance.user

        addresses_ids = user_data.pop('addresses_ids', [])
        user_types_ids = user_data.pop('user_types_ids', [])
        groups_ids = user_data.pop('groups_ids', [])

        # Atualizar campos do usuário
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        # Atualizar relações many-to-many
        if addresses_ids:
            user.addresses.set(addresses_ids)
        if user_types_ids:
            user.user_types.set(user_types_ids)
        if groups_ids:
            user.groups.set(groups_ids)

        # Atualizar campos do empregado
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SquadSerializer(BaseSerializer):
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
        from core.serializers import BoardSerializer
        return BoardSerializer(obj.boards, many=True).data
