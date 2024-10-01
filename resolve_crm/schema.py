import graphene
from graphene_django.types import DjangoObjectType
from .models import Lead, Task, Attachment, Contact, MarketingCampaign, ContractSubmission, Sale, Project, Payment, PaymentInstallment, Financier

class LeadType(DjangoObjectType):
    class Meta:
        model = Lead
        fields = "__all__"

class TaskType(DjangoObjectType):
    class Meta:
        model = Task
        fields = "__all__"

class AttachmentType(DjangoObjectType):
    class Meta:
        model = Attachment
        fields = "__all__"

class ContactType(DjangoObjectType):
    class Meta:
        model = Contact
        fields = "__all__"

class MarketingCampaignType(DjangoObjectType):
    class Meta:
        model = MarketingCampaign
        fields = "__all__"

class ContractSubmissionType(DjangoObjectType):
    class Meta:
        model = ContractSubmission
        fields = "__all__"

class SaleType(DjangoObjectType):
    class Meta:
        model = Sale
        fields = "__all__"

class ProjectType(DjangoObjectType):
    class Meta:
        model = Project
        fields = "__all__"

class PaymentType(DjangoObjectType):
    class Meta:
        model = Payment
        fields = "__all__"

class PaymentInstallmentType(DjangoObjectType):
    class Meta:
        model = PaymentInstallment
        fields = "__all__"

class FinancierType(DjangoObjectType):
    class Meta:
        model = Financier
        fields = "__all__"

class Query(graphene.ObjectType):
    leads = graphene.List(LeadType)
    tasks = graphene.List(TaskType)
    attachments = graphene.List(AttachmentType)
    contacts = graphene.List(ContactType)
    marketing_campaigns = graphene.List(MarketingCampaignType)
    contract_submissions = graphene.List(ContractSubmissionType)
    sales = graphene.List(SaleType)
    projects = graphene.List(ProjectType)
    payments = graphene.List(PaymentType)
    payment_installments = graphene.List(PaymentInstallmentType)
    financiers = graphene.List(FinancierType)

    def resolve_leads(self, info, **kwargs):
        return Lead.objects.all()

    def resolve_tasks(self, info, **kwargs):
        return Task.objects.all()

    def resolve_attachments(self, info, **kwargs):
        return Attachment.objects.all()

    def resolve_contacts(self, info, **kwargs):
        return Contact.objects.all()

    def resolve_marketing_campaigns(self, info, **kwargs):
        return MarketingCampaign.objects.all()

    def resolve_contract_submissions(self, info, **kwargs):
        return ContractSubmission.objects.all()

    def resolve_sales(self, info, **kwargs):
        return Sale.objects.all()

    def resolve_projects(self, info, **kwargs):
        return Project.objects.all()

    def resolve_payments(self, info, **kwargs):
        return Payment.objects.all()

    def resolve_payment_installments(self, info, **kwargs):
        return PaymentInstallment.objects.all()

    def resolve_financiers(self, info, **kwargs):
        return Financier.objects.all()

# Crie o schema com a query definida
schema = graphene.Schema(query=Query)
