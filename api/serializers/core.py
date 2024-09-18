from rest_framework.serializers import SerializerMethodField
from api.serializers.accounts import BaseSerializer
from core.models import *
from .accounts import BranchSerializer, RelatedUserSerializer, ContentTypeSerializer


class BoardSerializer(BaseSerializer):

    branch = BranchSerializer()
  
    class Meta:
        model = Board
        fields = '__all__'
        

class BoardStatusSerializer(BaseSerializer):
    
      class Meta:
          model = BoardStatus
          fields = '__all__'
          

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


