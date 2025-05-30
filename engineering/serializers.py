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


class SupplyAdequanceSerializer(BaseSerializer):
    class Meta:
        model = SupplyAdequance
        fields = '__all__'


class UnitsSerializer(BaseSerializer):
    def validate(self, data):
        instance = self.instance
        project = data.get('project') or (instance.project if instance else None)
        unit_percentage = data.get('unit_percentage') or (instance.unit_percentage if instance else 0)
        
        if project:
            total_percentage = Units.objects.filter(
                project=project
            ).exclude(id=instance.id if instance else None).aggregate(
                total=models.Sum('unit_percentage')
            )['total'] or 0
            
            if total_percentage + (unit_percentage or 0) > 100:
                raise ValidationError({
                    "unit_percentage": "A soma da porcentagem das unidades não pode ser superior a 100%"
                })
        return data
    
    class Meta:
        model = Units
        fields = '__all__'


class RequestsEnergyCompanySerializer(BaseSerializer):
    class Meta:
        model = RequestsEnergyCompany
        fields = '__all__'
        
        
        
class CivilConstructionSerializer(BaseSerializer):
    class Meta:
        model = CivilConstruction
        fields = '__all__'