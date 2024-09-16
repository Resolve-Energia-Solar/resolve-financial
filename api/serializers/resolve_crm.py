from rest_framework.serializers import ModelSerializer, SerializerMethodField
from resolve_crm.models import *
from api.serializers.accounts import RelatedUserSerializer, AddressSerializer,  ContentTypeSerializer, BranchSerializer


class BaseSerializer(ModelSerializer):
    
    class Meta:
        model = None
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'is_deleted' in self.fields:
            self.fields.pop('is_deleted')


class LeadSerializer(BaseSerializer):
  
    seller = RelatedUserSerializer()
    sdr = RelatedUserSerializer()
    addresses = AddressSerializer(many=True)
    
    class Meta:
        model = Lead
        fields = '__all__'
        
        
class TaskSerializer(BaseSerializer):
      
    lead = LeadSerializer()
    members = RelatedUserSerializer(many=True)
    
    class Meta:
        model = Task
        fields = '__all__'


class AttachmentSerializer(BaseSerializer):
    content_type = ContentTypeSerializer()
    
    class Meta:
        model = Attachment
        fields = '__all__'
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['file'] = instance.file.url
        return data

class MarketingCampaignSerializer(BaseSerializer):
    
    class Meta:
        model = MarketingCampaign
        fields = '__all__'
    

class SaleSerializer(BaseSerializer):
    
    lead = LeadSerializer()
    seller = RelatedUserSerializer()
    sales_supervisor = RelatedUserSerializer()
    sales_manager = RelatedUserSerializer()
    branch = BranchSerializer()
    marketing_campaign = MarketingCampaignSerializer()
    
    class Meta:
        model = Sale
        fields = '__all__'


class FinancierSerializer(BaseSerializer):
    
    address = AddressSerializer()
    
    class Meta:
        model = Financier
        fields = '__all__'