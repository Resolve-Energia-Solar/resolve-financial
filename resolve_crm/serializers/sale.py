# Em serializers.py

from rest_framework import serializers
from ..models import Sale

class SaleListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.complete_name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    documents_under_analysis_count = serializers.IntegerField(read_only=True)
    projects_info = serializers.SerializerMethodField()
    final_service_opinion = serializers.SerializerMethodField()
    signature_status = serializers.SerializerMethodField()
    is_released_to_engineering = serializers.BooleanField(read_only=True)

    class Meta:
        model = Sale
        fields = [
            'id',
            'contract_number',
            'total_value',
            'status',
            'signature_date',
            'is_pre_sale',
            'created_at',
            'customer_name',
            'branch_name',
            'documents_under_analysis_count',
            'projects_info',
            'final_service_opinion',
            'signature_status',
            'is_released_to_engineering',
        ]

    def get_projects_info(self, obj):
        projects = getattr(obj, 'cached_projects', [])
        return [
            {
                "id": p.id,
                "project_number": p.project_number,
                "journey_counter": getattr(p, 'journey_counter', 0)
            }
            for p in projects
        ]

    def get_final_service_opinion(self, obj):
        projects = getattr(obj, 'cached_projects', [])
        opinions = [
            {
                "id": p.inspection.final_service_opinion.id,
                "name": p.inspection.final_service_opinion.name,
            }
            for p in projects
            if p.inspection and p.inspection.final_service_opinion
        ]
        return opinions[0] if opinions else None

    def get_signature_status(self, obj):
        submissions = getattr(obj, "all_submissions", [])
        statuses = {s.status for s in submissions}

        if not obj.signature_date:
            if not statuses: return "Pendente"
            if "P" in statuses and "A" not in statuses: return "Enviado"
            if "A" in statuses: return "Assinado"
            if "R" in statuses: return "Recusado"
        return "Assinado"