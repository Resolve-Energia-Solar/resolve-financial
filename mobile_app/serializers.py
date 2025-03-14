from collections import defaultdict

from django.utils.text import slugify
from .models import *
from resolve_crm.serializers import ContractSubmissionSerializer
from rest_framework.reverse import reverse
from rest_framework.serializers import SerializerMethodField, StringRelatedField
from accounts.models import User
from accounts.serializers import AddressSerializer
from api.serializers import BaseSerializer
from engineering.models import RequestsEnergyCompany
from engineering.serializers import UnitsSerializer
from field_services.models import Schedule
from resolve_crm.models import Project, Sale


class CustomerSerializer(BaseSerializer):
    sales_urls = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'person_type', 'complete_name', 'email', 'birth_date', 'first_document', 'profile_picture', 'phone_numbers', 'sales_urls']

    
    def get_sales_urls(self, obj):
        request = self.context.get('request')
        return [
            reverse('mobile_app:mobile_sale-detail', args=[sale.id], request=request)
            for sale in obj.customer_sales.all()
        ]


class MobileSaleSerializer(BaseSerializer):
    projects_urls = SerializerMethodField(read_only=True)
    contract_submission = SerializerMethodField(read_only=True)
    financial_url = SerializerMethodField(read_only=True)
    
    class Meta:
        model = Sale
        fields = '__all__'

    def get_projects_urls(self, obj):
        request = self.context.get('request')
        return [
            reverse('mobile_app:mobile_project-detail', args=[project.id], request=request)
            for project in obj.projects.all()
        ]
    
    def get_contract_submission(self, obj):
        contract_submission = obj.contract_submissions.all().order_by('-submit_datetime').first()
        if contract_submission:
            data = ContractSubmissionSerializer(contract_submission).data
            data.pop('sale', None)
            return data
        return None

    def get_financial_url(self, obj):
        request = self.context.get('request')
        return reverse('mobile_app:financial', args=[obj.id], request=request)


class MobileProjectSerializer(BaseSerializer):

    deadlines = SerializerMethodField(read_only=True)
    field_services_urls = SerializerMethodField(read_only=True)
    requests_energy_company_urls = SerializerMethodField(read_only=True)
    contract_url = SerializerMethodField(read_only=True)
    monitoring_url = SerializerMethodField(read_only=True)
    address = SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'start_date', 'product', 'project_number', 'address', 'deadlines', 'contract_url', 'field_services_urls', 'requests_energy_company_urls', 'monitoring_url']

    def get_address(self, obj):
        if obj.address:
            return AddressSerializer(obj.address).data
        return None

    def get_deadlines(self, obj):
        excluded_slugs = {"documentacao", "financeiro", "project"}

        field_service_slugs = {
            slugify(field_service.service) 
            for field_service in obj.field_services.all()
        }
        request_energy_slugs = {
            slugify(request_energy_company.type) 
            for request_energy_company in obj.requests_energy_company.all()
        }

        # Filtrar prazos
        return [
            {
                'step': step.step.name,
                'deadline': step.deadline,
                'slug': step.step.slug
            }
            for step in obj.project_steps.all().order_by('deadline')
            if slugify(step.step.slug) not in excluded_slugs and
               slugify(step.step.name) not in field_service_slugs | request_energy_slugs
        ]

    def get_contract_url(self, obj):
        request = self.context.get('request')
        return reverse('mobile_app:documentation', args=[obj.id], request=request)

    def get_field_services_urls(self, obj):
        request = self.context.get('request')
        grouped_urls = defaultdict(list)

        # Agrupando e ordenando os serviços de campo
        for field_service in obj.field_services.all().order_by('-created_at'):
            service_slug = slugify(field_service.service)
            url = reverse('mobile_app:field_service-detail', args=[field_service.id], request=request)
            grouped_urls[service_slug].append(url)

        return grouped_urls

    def get_requests_energy_company_urls(self, obj):
        request = self.context.get('request')
        grouped_urls = defaultdict(list)

        # Agrupando e ordenando solicitações de concessionárias
        for request_energy_company in obj.requests_energy_company.all().order_by('-created_at'):
            type_slug = slugify(request_energy_company.type)
            url = reverse('mobile_app:requests_energy_company-detail', args=[request_energy_company.id], request=request)
            grouped_urls[type_slug].append(url)

        return grouped_urls

    def get_monitoring_url(self, obj):
        request = self.context.get('request')
        if obj.plant_integration:
            return reverse('mobile_app:monitoring-detail', args=[obj.plant_integration], request=request)
        return None


class FieldServiceSerializer(BaseSerializer):

    service = StringRelatedField(read_only=True)
    
    class Meta:
        model = Schedule
        fields = ['service', 'schedule_agent', 'schedule_date', 'schedule_start_time', 'schedule_end_time', 'going_to_location_at', 'execution_started_at', 'execution_finished_at', 'status', 'created_at']
        ordering = ['schedule_date', 'schedule_start_time']


class RequestsEnergyCompanySerializer(BaseSerializer):

    # Para leitura: usar serializador completo
    unit = UnitsSerializer(read_only=True)
    type = StringRelatedField(read_only=True)

    class Meta:
        model = RequestsEnergyCompany
        fields = [
            'unit', 'type', 'situation', 'request', 'request_date',
            'status', 'conclusion_date', 'interim_protocol',
            'final_protocol', 'created_at'
        ]


class APISerializer(BaseSerializer):
    class Meta:
        model = API
        fields = '__all__'


class DiscountSerializer(BaseSerializer):
    class Meta:
        model = Discount
        fields = '__all__'


class ReelSerializer(BaseSerializer):
    class Meta:
        model = Reel
        fields = '__all__'


class MediaSerializer(BaseSerializer):
    class Meta:
        model = Media
        fields = '__all__'


class ProductSerializer(BaseSerializer):
    class Meta:
        model = Product
        fields = '__all__'
