from collections import defaultdict

from django.utils.text import slugify
from rest_framework.reverse import reverse
from rest_framework.serializers import SerializerMethodField, StringRelatedField

from accounts.models import User
from accounts.serializers import PhoneNumberSerializer, RelatedUserSerializer
from api.serializers import BaseSerializer
from engineering.models import RequestsEnergyCompany
from engineering.serializers import UnitsSerializer
from inspections.models import Schedule
from resolve_crm.models import Project, Sale


class CustomerSerializer(BaseSerializer):

    phone_numbers = PhoneNumberSerializer(many=True, read_only=True)
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

    customer = RelatedUserSerializer(read_only=True)
    seller = RelatedUserSerializer(read_only=True)
    sales_supervisor = RelatedUserSerializer(read_only=True)
    sales_manager = RelatedUserSerializer(read_only=True)
    projects_urls = SerializerMethodField(read_only=True)
    
    class Meta:
        model = Sale
        fields = ['id', 'contract_number', 'customer', 'seller', 'sales_supervisor', 'sales_manager', 'status', 'created_at', 'total_value', 'signature_date', 'branch', 'is_pre_sale', 'projects_urls']

    def get_projects_urls(self, obj):
        request = self.context.get('request')
        return [
            reverse('mobile_app:mobile_project-detail', args=[project.id], request=request)
            for project in obj.projects.all()
        ]


class MobileProjectSerializer(BaseSerializer):

    field_services_urls = SerializerMethodField(read_only=True)
    requests_energy_company_urls = SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'product', 'project_number', 'field_services_urls', 'requests_energy_company_urls']

    def get_field_services_urls(self, obj):
        request = self.context.get('request')
        grouped_urls = defaultdict(list)

        # Grouping and ordering field services
        for field_service in obj.field_services.all().order_by('-created_at'):
            service_slug = slugify(field_service.service)
            url = reverse('mobile_app:field_service-detail', args=[field_service.id], request=request)
            grouped_urls[service_slug].append(url)

        return grouped_urls

    def get_requests_energy_company_urls(self, obj):
        request = self.context.get('request')
        grouped_urls = defaultdict(list)

        # Grouping and ordering requests energy company
        for request_energy_company in obj.requests_energy_company.all().order_by('-created_at'):
            type_slug = slugify(request_energy_company.type)
            url = reverse('mobile_app:requests_energy_company-detail', args=[request_energy_company.id], request=request)
            grouped_urls[type_slug].append(url)

        return grouped_urls


class FieldServiceSerializer(BaseSerializer):

    service = StringRelatedField(read_only=True)
    schedule_agent = RelatedUserSerializer(read_only=True)
    
    class Meta:
        model = Schedule
        fields = ['service', 'schedule_agent', 'schedule_date', 'schedule_start_time', 'schedule_end_time', 'going_to_location_at', 'execution_started_at', 'execution_finished_at', 'status']
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
