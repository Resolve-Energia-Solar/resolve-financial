from engineering.models import *
from api.serializers import BaseSerializer
from rest_framework import serializers


class SituationEnergyCompanySerializer(BaseSerializer):
    class Meta:
        model = SituationEnergyCompany
        fields = '__all__'
        

class ResquestTypeSerializer(BaseSerializer):
    class Meta:
        model = ResquestType
        fields = '__all__'
    

class EnergyCompanySerializer(BaseSerializer):
    class Meta:
        model = EnergyCompany
        fields = '__all__'

class ProjectReadSerializer(BaseSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class SupplyAdequanceSerializer(BaseSerializer):
    class Meta:
        model = SupplyAdequance
        fields = '__all__'


class UnitsSerializer(BaseSerializer):    
    def validate(self, data):
        project = data.get('project') or (self.instance.project if self.instance else None)
        unit_percentage = data.get('unit_percentage') or (self.instance.unit_percentage if self.instance else 0)
        total_percentage = Units.objects.filter(project=project)
        if self.instance:
            total_percentage = total_percentage.exclude(id=self.instance.id)
        total_percentage = total_percentage.aggregate(total=models.Sum('unit_percentage'))['total'] or 0
        if total_percentage + (unit_percentage or 0) > 100:
            raise ValidationError({"unit_percentage": "A soma da porcentagem das unidades não pode ser superior a 100%"})
        return data
    
    class Meta:
        model = Units
        fields = '__all__'


class RequestsEnergyCompanySerializer(BaseSerializer):
    str = serializers.SerializerMethodField()
    class Meta:
        model = RequestsEnergyCompany
        fields = '__all__'
        
    def get_str(self, obj):
        return str(obj)
