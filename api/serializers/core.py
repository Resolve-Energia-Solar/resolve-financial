from rest_framework.serializers import SerializerMethodField
from api.serializers.accounts import BaseSerializer
from core.models import *
from .accounts import BranchSerializer, RelatedUserSerializer, ContentTypeSerializer
from resolve_crm.models import Lead


class ColumnNameSerializer(BaseSerializer):
        
        class Meta:
            model = Column
            fields = ['id', 'name']

class ReadLeadSerializer(BaseSerializer):
    
    column = ColumnNameSerializer()
    
    class Meta:
        model = Lead
        fields = ['id', 'name', 'column' , 'contact_email', 'phone','seller','created_at']


class ColumnSerializer(BaseSerializer):
    
    leads = ReadLeadSerializer(many=True)
    
    class Meta:
        model = Column
        fields = ['id', 'name', 'board', 'leads']


class BoardSerializer(BaseSerializer):
    
    columns = ColumnSerializer(many=True)
    branch = BranchSerializer()
  
    class Meta:
        model = Board
        fields = ['id', 'title', 'description', 'columns', 'branch']
    

class TaskSerializer(BaseSerializer):
  
      owner = RelatedUserSerializer()
      board = BoardSerializer()
      content_type = ContentTypeSerializer()
      depends_on = SerializerMethodField()
      
      class Meta:
          model = Task
          fields = '__all__'
          
      def get_depends_on(self, obj):
          return TaskSerializer(obj.depends_on, many=True).data
        