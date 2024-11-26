from accounts.models import User
from api.serializers import BaseSerializer
from accounts.serializers import PhoneNumberSerializer, RelatedUserSerializer
from inspections.models import Schedule, Service
from inspections.serializers import ServiceSerializer
from resolve_crm.models import Project, Sale
from rest_framework.serializers import SerializerMethodField, StringRelatedField
from rest_framework.reverse import reverse


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
            reverse('api:project-detail', args=[project.id], request=request)
            for project in obj.projects.all()
        ]


class MobileProjectSerializer(BaseSerializer):

    class Meta:
        model = Project
        fields = ['id', 'product', 'project_number']


class FieldServiceSerializer(BaseSerializer):

    service = StringRelatedField(read_only=True)
    schedule_agent = RelatedUserSerializer(read_only=True)
    
    class Meta:
        model = Schedule
        fields = ['service', 'schedule_agent', 'schedule_date', 'schedule_start_time', 'schedule_end_time', 'going_to_location_at', 'execution_started_at', 'execution_finished_at', 'status']
        ordering = ['schedule_date', 'schedule_start_time']