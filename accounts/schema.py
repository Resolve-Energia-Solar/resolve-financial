import graphene
from graphene_django.types import DjangoObjectType
from .models import UserType, User, PhoneNumber, Address, Branch, Department, Role, Squad

# Define um tipo para UserType
class UserTypeType(DjangoObjectType):
    class Meta:
        model = UserType
        fields = '__all__'

# Define um tipo para User
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = '__all__'

# Define um tipo para PhoneNumber
class PhoneNumberType(DjangoObjectType):
    class Meta:
        model = PhoneNumber
        fields = '__all__'

# Define um tipo para Address
class AddressType(DjangoObjectType):
    class Meta:
        model = Address
        fields = '__all__'

# Define um tipo para Branch
class BranchType(DjangoObjectType):
    class Meta:
        model = Branch
        fields = '__all__'

# Define um tipo para Department
class DepartmentType(DjangoObjectType):
    class Meta:
        model = Department
        fields = '__all__'

# Define um tipo para Role
class RoleType(DjangoObjectType):
    class Meta:
        model = Role
        fields = '__all__'

# Define um tipo para Squad
class SquadType(DjangoObjectType):
    class Meta:
        model = Squad
        fields = '__all__'

# Define as queries
class Query(graphene.ObjectType):
    all_user_types = graphene.List(UserTypeType)
    all_users = graphene.List(UserType)
    all_phone_numbers = graphene.List(PhoneNumberType)
    all_addresses = graphene.List(AddressType)
    all_branches = graphene.List(BranchType)
    all_departments = graphene.List(DepartmentType)
    all_roles = graphene.List(RoleType)
    all_squads = graphene.List(SquadType)

    def resolve_all_user_types(self, info):
        return UserType.objects.all()

    def resolve_all_users(self, info):
        return User.objects.all()

    def resolve_all_phone_numbers(self, info):
        return PhoneNumber.objects.all()

    def resolve_all_addresses(self, info):
        return Address.objects.all()

    def resolve_all_branches(self, info):
        return Branch.objects.all()

    def resolve_all_departments(self, info):
        return Department.objects.all()

    def resolve_all_roles(self, info):
        return Role.objects.all()

    def resolve_all_squads(self, info):
        return Squad.objects.all()

# Define o schema
schema = graphene.Schema(query=Query)
