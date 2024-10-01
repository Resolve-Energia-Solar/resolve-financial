import graphene
from graphene_django.types import DjangoObjectType
from .models import PaymentRequest, SaleResume, UserDepartment, AppsheetUser

class PaymentRequestType(DjangoObjectType):
    class Meta:
        model = PaymentRequest
        fields = "__all__"

class SaleResumeType(DjangoObjectType):
    class Meta:
        model = SaleResume
        fields = "__all__"

class UserDepartmentType(DjangoObjectType):
    class Meta:
        model = UserDepartment
        fields = "__all__"

class AppsheetUserType(DjangoObjectType):
    class Meta:
        model = AppsheetUser
        fields = "__all__"

class Query(graphene.ObjectType):
    payment_requests = graphene.List(PaymentRequestType)
    sale_resumes = graphene.List(SaleResumeType)
    user_departments = graphene.List(UserDepartmentType)
    appsheet_users = graphene.List(AppsheetUserType)

    def resolve_payment_requests(self, info, **kwargs):
        return PaymentRequest.objects.all()

    def resolve_sale_resumes(self, info, **kwargs):
        return SaleResume.objects.all()

    def resolve_user_departments(self, info, **kwargs):
        return UserDepartment.objects.all()

    def resolve_appsheet_users(self, info, **kwargs):
        return AppsheetUser.objects.all()

# Crie o schema com a query definida
schema = graphene.Schema(query=Query)
