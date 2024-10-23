from accounts.models import Address, User
from api.serializers.core import ColumnSerializer
from core.models import Column
from financial.models import Financier
from resolve_crm.models import *
from api.serializers.accounts import RelatedUserSerializer, AddressSerializer,  ContentTypeSerializer, BranchSerializer
from api.serializers.accounts import BaseSerializer
from api.serializers.logistics import MaterialsSerializer
from logistics.models import Materials, ProjectMaterials
from rest_framework.serializers import PrimaryKeyRelatedField

 
class LeadSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    customer = RelatedUserSerializer(read_only=True)
    seller = RelatedUserSerializer(read_only=True, allow_null=True)
    sdr = RelatedUserSerializer(read_only=True, allow_null=True)
    addresses = AddressSerializer(many=True, read_only=True)
    column = ColumnSerializer(read_only=True)

    # Para escrita: usar apenas IDs
    seller_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='seller', allow_null=True)
    sdr_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='sdr', allow_null=True)
    addresses_ids = PrimaryKeyRelatedField(queryset=Address.objects.all(), many=True, write_only=True, source='addresses')
    column_id = PrimaryKeyRelatedField(queryset=Column.objects.all(), write_only=True, source='column')

    class Meta:
        model = Lead
        depth = 1
        fields = '__all__'


class LeadTaskSerializer(BaseSerializer):
    
    # Para leitura: usar serializadores completos  
    members = RelatedUserSerializer(many=True, read_only=True)
    # lead = LeadSerializer(read_only=True)
    
    # Para escrita: usar apenas IDs
    members_ids = PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, write_only=True, source='members')
    # lead_id = PrimaryKeyRelatedField(queryset=Lead.objects.all(), write_only=True, source='lead')
    
    class Meta:
        model = Task
        fields = '__all__'


class AttachmentSerializer(BaseSerializer):
    
    # Para leitura: usar serializadores completos
    content_type = ContentTypeSerializer(read_only=True)
    
    # Para escrita: usar apenas ID
    content_type_id = PrimaryKeyRelatedField(queryset=ContentType.objects.all(), write_only=True, source='content_type')
    
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
    # Para leitura: usar serializadores completos
    customer = RelatedUserSerializer(read_only=True)
    seller = RelatedUserSerializer(read_only=True)
    sales_supervisor = RelatedUserSerializer(read_only=True)
    sales_manager = RelatedUserSerializer(read_only=True)
    branch = BranchSerializer(read_only=True)
    marketing_campaign = MarketingCampaignSerializer(read_only=True)
    lead = LeadSerializer(read_only=True)

    # Para escrita: usar apenas IDs
    customer_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='customer')
    seller_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='seller')
    sales_supervisor_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='sales_supervisor')
    sales_manager_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='sales_manager')
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, source='branch')
    marketing_campaign_id = PrimaryKeyRelatedField(queryset=MarketingCampaign.objects.all(), write_only=True, source='marketing_campaign')
    lead_id = PrimaryKeyRelatedField(queryset=Lead.objects.all(), write_only=True, source='lead')

    class Meta:
        model = Sale
        fields = '__all__'


class ProjectSerializer(BaseSerializer):
    # Para leitura: usar serializadores completos
    sale = SaleSerializer(read_only=True)
    materials = MaterialsSerializer(many=True, read_only=True)
    designer = RelatedUserSerializer(read_only=True)
    homologator = RelatedUserSerializer(read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)

    # Para escrita: usar apenas IDs
    sale_id = PrimaryKeyRelatedField(queryset=Sale.objects.all(), write_only=True, source='sale')
    designer_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='designer')
    homologator_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='homologator')
    addresses_ids = PrimaryKeyRelatedField(queryset=Address.objects.all(), many=True, write_only=True, source='addresses')

    class Meta:
        model = Project
        fields = '__all__'

    def get_materials(self, obj):
        return MaterialsSerializer(obj.materials.all(), many=True).data