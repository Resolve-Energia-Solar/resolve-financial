from rest_framework.serializers import SerializerMethodField, PrimaryKeyRelatedField
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from api.serializers import BaseSerializer
from accounts.models import *
from rest_framework import serializers
from validate_docbr import CPF, CNPJ


class DepartmentSerializer(BaseSerializer):

    owner_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='owner')

    class Meta:
        model = Department
        exclude = ['is_deleted', 'owner']

        
class RoleSerializer(BaseSerializer):
    class Meta:
        model = Role
        exclude = ['is_deleted']


class PhoneNumberSerializer(BaseSerializer):
    user = SerializerMethodField(read_only=True)  # Apenas leitura
    user_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='user', required=False)  # Apenas escrita

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
    employee_data = SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'profile_picture', 'complete_name', 'birth_date', 'first_document', 'email', 'phone_numbers', 'employee', 'employee_data']

    def get_employee_data(self, obj):
        return obj.employee_data() if hasattr(obj, 'employee') else None

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
        ordering = ['app_label', 'model']


class PermissionSerializer(BaseSerializer):
    # Para leitura: usar serializador completo
    content_type = ContentTypeSerializer(read_only=True)

    # Para escrita: usar apenas ID
    content_type_id = PrimaryKeyRelatedField(queryset=ContentType.objects.all().order_by('app_label', 'model'), write_only=True, source='content_type')

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


class CustomFieldSerializer(BaseSerializer):
    user = SerializerMethodField(read_only=True)
    user_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)

    class Meta:
        model = CustomField
        fields = '__all__'

    def create(self, validated_data):
        # Pop the user_id from validated_data and set it as the related user
        user = validated_data.pop('user_id')
        instance = CustomField.objects.create(user=user, **validated_data)
        return instance

    def get_user(self, obj):
        return obj.user.id if obj.user else None


class EmployeeSerializer(BaseSerializer):

    user = RelatedUserSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    branch = BranchSerializer(read_only=True)
    role = RoleSerializer(read_only=True)
    manager = SerializerMethodField()
    
    user_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='user')
    department_id = PrimaryKeyRelatedField(queryset=Department.objects.all(), write_only=True, source='department')
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, source='branch')
    role_id = PrimaryKeyRelatedField(queryset=Role.objects.all(), write_only=True, source='role')
    user_manager_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='user_manager', required=False)

    class Meta:
        model = Employee
        fields = '__all__'
        
    def get_manager(self, obj):
        try:
            return RelatedUserSerializer(obj.user_manager).data
        except:
            return None
        
    def create(self, validated_data):
        user_data = validated_data.pop('user', None)
        addresses = []
        user_types = []
        groups = []

        if isinstance(user_data, dict):
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
        else:
            user = user_data  # Assuma que é um objeto User já existente

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


class UserSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    addresses = AddressSerializer(many=True, read_only=True)
    user_types = UserTypeSerializer(many=True, read_only=True)
    groups = GroupSerializer(many=True, read_only=True)
    phone_numbers = PhoneNumberSerializer(many=True, read_only=True)
    employee = EmployeeSerializer(read_only=True)
    employee_data = SerializerMethodField()

    # Para escrita: usar apenas IDs
    addresses_ids = PrimaryKeyRelatedField(queryset=Address.objects.all(), many=True, write_only=True, source='addresses', allow_null=True)
    user_types_ids = PrimaryKeyRelatedField(queryset=UserType.objects.all(), many=True, write_only=True, source='user_types', allow_null=True)
    groups_ids = PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True, write_only=True, source='groups', allow_null=True, required=False)
    phone_numbers_ids = PrimaryKeyRelatedField(queryset=PhoneNumber.objects.all(), many=True, write_only=True, source='phone_numbers', allow_null=True, required=False)

    user_permissions = SerializerMethodField()
    distance = SerializerMethodField()
    daily_schedules_count = SerializerMethodField()

    class Meta:
        model = User
        exclude = ['password']
        
    def validate(self, attrs):
        if 'first_document' in attrs:
            attrs['first_document'] = self.validate_first_document(attrs['first_document'])
        
        return super().validate(attrs)
        
    def validate_first_document(self, value):
        value = value.replace('.', '').replace('-', '').replace('/', '')

        # Verifica se é um CPF ou CNPJ válido
        if len(value) == 11:  # CPF
            if not CPF().validate(value):
                raise serializers.ValidationError("CPF inválido.")
        elif len(value) == 14:  # CNPJ
            if not CNPJ().validate(value):
                raise serializers.ValidationError("CNPJ inválido.")
        else:
            raise serializers.ValidationError("Número inválido. Insira um CPF ou CNPJ válido.")

        # Verifica se está criando um novo usuário ou alterando o CPF/CNPJ
        if self.instance:
            # Se for edição, verifica se o CPF/CNPJ foi alterado
            if self.instance.first_document != value:
                user_exists = User.objects.filter(first_document=value).exists()
                if user_exists:
                    raise serializers.ValidationError("CPF/CNPJ já cadastrado.")
        else:
            # Caso seja criação de um novo usuário
            user_exists = User.objects.filter(first_document=value).exists()
            if user_exists:
                raise serializers.ValidationError("CPF/CNPJ já cadastrado.")

        return value
        
    def get_employee_data(self, obj):
        return obj.employee_data() if hasattr(obj, 'employee') else None
    
    def get_user_permissions(self, obj):
        return obj.get_all_permissions()
    
    def get_distance(self, obj):
        return getattr(obj, 'distance', None)
    
    def get_daily_schedules_count(self, obj):
        return getattr(obj, 'daily_schedules_count', None)
    

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


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    uid = serializers.IntegerField()
    new_password = serializers.CharField(min_length=8)