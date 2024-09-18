from rest_framework.serializers import SerializerMethodField
from api.serializers.accounts import BaseSerializer
from core.models import *
from .accounts import BranchSerializer, RelatedUserSerializer, ContentTypeSerializer
from resolve_crm.models import Lead


class ReadLeadSerializer(BaseSerializer):
    
    detail_api_url = SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = ['id', 'name', 'contact_email', 'phone', 'status','seller','created_at', 'detail_api_url']
        
    def get_detail_api_url(self, obj):
        return obj.get_detail_api_url()


class BoardStatusSerializer(BaseSerializer):
    
    order = SerializerMethodField()
    
    class Meta:
        model = BoardStatus
        fields = '__all__'
          
    def get_order(self, obj):
        board = self.context.get('board')
        order = BoardStatusesOrder.objects.get(board=board, status=obj).order if board else None
        return order


class BoardSerializer(BaseSerializer):
    
    leads = ReadLeadSerializer(many=True)
    branch = BranchSerializer()
    statuses = SerializerMethodField()
  
    class Meta:
        model = Board
        fields = '__all__'
        
    def get_statuses(self, obj):
        return BoardStatusSerializer(obj.statuses, many=True, context={'board': obj}).data
        


class TaskSerializer(BaseSerializer):
  
      owner = RelatedUserSerializer()
      board = BoardSerializer()
      status = BoardStatusSerializer()
      content_type = ContentTypeSerializer()
      depends_on = SerializerMethodField()
      
      class Meta:
          model = Task
          fields = '__all__'
          
      def get_depends_on(self, obj):
          return TaskSerializer(obj.depends_on, many=True).data
        