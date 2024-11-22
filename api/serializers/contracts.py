from contracts.models import *
from rest_framework import serializers

class DocumentSubTypeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = DocumentSubType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentTypeSerializer(serializers.ModelSerializer):
    subtypes = DocumentSubTypeSerializer(many=True, read_only=True)
    
    class Meta:
        model = DocumentType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['app_label'] = instance.get_app_label_display()
        return data
    