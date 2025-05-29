from rest_framework.serializers import SerializerMethodField, PrimaryKeyRelatedField
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from api.serializers import BaseSerializer
from accounts.models import *
from rest_framework import serializers
from validate_docbr import CPF, CNPJ
from datetime import date


class DepartmentSerializer(BaseSerializer):
    class Meta:
        model = Department
        fields = '__all__'

        
class RoleSerializer(BaseSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class PhoneNumberSerializer(BaseSerializer):
    class Meta:
        model = PhoneNumber
        fields = '__all__'

    # def create(self, validated_data):
    #     user = validated_data.pop('user', None)
    #     phone_number = PhoneNumber.objects.create(user=user, **validated_data)
    #     return phone_number


class AddressSerializer(BaseSerializer):
    
    complete_address = SerializerMethodField()
    user = PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, required=False,
    )
    
    class Meta:
        model = Address
        fields = '__all__'
        
    def get_complete_address(self, obj):
        address = f"{obj.street} - {obj.number}"
        if obj.complement:
            address += f", {obj.complement}"
        address += f", {obj.city}/{obj.state}"
        if obj.zip_code:
            address += f" - {obj.zip_code}"
        address += f", {obj.country}"
        if obj.neighborhood:
            address += f", {obj.neighborhood}"
        return address

    def create(self, validated_data):
        if 'user' in validated_data:
            user = validated_data.pop('user')
            address = Address.objects.create(**validated_data)
            user.addresses.add(address)
            return address
        return Address.objects.create(**validated_data)


class BranchSerializer(BaseSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


class ContentTypeSerializer(BaseSerializer):
    class Meta:
        model = ContentType
        fields = '__all__'
        ordering = ['app_label', 'model']


class PermissionSerializer(BaseSerializer):
    class Meta:
        model = Permission
        fields = '__all__'


class GroupSerializer(BaseSerializer):
    class Meta:
        model = Group
        fields = '__all__'

class UserTypeSerializer(BaseSerializer):
        
        class Meta:
            model = UserType
            fields = '__all__'


class CustomFieldSerializer(BaseSerializer):
    class Meta:
        model = CustomField
        fields = '__all__'

    # def create(self, validated_data):
    #     user = validated_data.pop('user')
    #     instance = CustomField.objects.create(user=user, **validated_data)
    #     return instance


class EmployeeSerializer(BaseSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
        
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
        # Remover o campo many-to-many do dicionário
        related_branches = validated_data.pop('related_branches', None)
        
        user_data = validated_data.pop('user', {})
        if not isinstance(user_data, dict):
            user_data = {}
        user = instance.user

        addresses = user_data.pop('addresses', [])
        user_types = user_data.pop('user_types', [])
        groups = user_data.pop('groups', [])

        # Atualizar campos do usuário
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        # Atualizar campos do empregado (exceto many-to-many)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Atualizar o many-to-many 'related_branches', se fornecido
        if related_branches is not None:
            instance.related_branches.set(related_branches)

        return instance


class UserSerializer(BaseSerializer):
    employee_data = SerializerMethodField()
    phone_numbers_ids = PrimaryKeyRelatedField(queryset=PhoneNumber.objects.all(), many=True, write_only=True, source='phone_numbers', allow_null=True, required=False)

    distance = SerializerMethodField()
    daily_schedules_count = SerializerMethodField()

    class Meta:
        model = User
        exclude = ['password', 'user_permissions', 'groups']
        
    def validate(self, attrs):
        if 'first_document' in attrs:
            attrs['first_document'] = self.validate_first_document(attrs['first_document'])
        
        birth_date = attrs.get('birth_date')
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                raise serializers.ValidationError("Usuários devem ter pelo menos 18 anos.")
                
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
    
    def get_distance(self, obj):
        return getattr(obj, 'distance', None)

    def get_daily_schedules_count(self, obj):
        return getattr(obj, 'daily_schedules_count', None)
    

class SquadSerializer(BaseSerializer):
    class Meta:
        model = Squad
        fields = '__all__'


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    uid = serializers.IntegerField()
    new_password = serializers.CharField(min_length=8)
    
    
class UserTypeSerializer(BaseSerializer):
    class Meta:
        model = UserType
        fields = '__all__'


class UserLoginSerializer(serializers.ModelSerializer):
    employee_data = serializers.SerializerMethodField()
    groups = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)
    user_permissions = serializers.SerializerMethodField()
    employee = SerializerMethodField()

    class Meta:
        model = User
        exclude = ['password',]
    
    def get_employee(self, obj):
        if not obj.employee:
            return None
        return {
            'id': obj.employee.id,
            'role': {
                'id': getattr(obj.employee.role, 'id', None),
                'name': getattr(obj.employee.role, 'name', None)
            } if obj.employee.role else None,
            'department': {
                'id': getattr(obj.employee.department, 'id', None),
                'name': getattr(obj.employee.department, 'name', None)
            } if obj.employee.department else None,
            'branch': getattr(obj.employee.branch, 'id', None),
            'user_manager': {
                'id': getattr(obj.employee.user_manager, 'id', None),
                'complete_name': getattr(obj.employee.user_manager, 'complete_name', None)
            } if obj.employee.user_manager else None,
        }
        

    def get_employee_data(self, obj):
        if not obj.employee:
            return None
        return {
            'id': obj.employee.id,
            'role': getattr(obj.employee.role, 'name', None),
            'department': getattr(obj.employee.department, 'name', None),
            'user_manager': {
                'id': getattr(obj.employee.user_manager, 'id', None),
                'complete_name': getattr(obj.employee.user_manager, 'complete_name', None)
            } if obj.employee.user_manager else None,
        }

    def get_user_permissions(self, obj):
        return list(obj.get_all_permissions())
