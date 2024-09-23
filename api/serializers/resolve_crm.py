from resolve_crm.models import *
from api.serializers.accounts import RelatedUserSerializer, AddressSerializer,  ContentTypeSerializer, BranchSerializer
from api.serializers.accounts import BaseSerializer
from api.serializers.logistics import MaterialsSerializer
from logistics.models import Materials, ProjectMaterials


class LeadSerializer(BaseSerializer):
  
    seller = RelatedUserSerializer(required=False, allow_null=True)
    sdr = RelatedUserSerializer(required=False, allow_null=True)
    addresses = AddressSerializer(many=True, required=False)
    
    class Meta:
        model = Lead
        fields = '__all__'

        
class LeadTaskSerializer(BaseSerializer):
      
    # lead = LeadSerializer()
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


class ProjectSerializer(BaseSerializer):
    
    sale = SaleSerializer()
    materials = MaterialsSerializer(many=True, read_only=True)
    designer = RelatedUserSerializer()
    homologator = RelatedUserSerializer()
    addresses = AddressSerializer(many=True)
    
    class Meta:
        model = Project
        fields = '__all__'
        
    def get_materials(self, obj):
        return ProjectMaterials.objects.filter(project=obj)