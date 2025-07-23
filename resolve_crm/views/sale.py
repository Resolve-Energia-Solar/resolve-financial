# Em views.py

from rest_framework.viewsets import ReadOnlyModelViewSet
from django.db.models import Count, Q, Prefetch, Sum, OuterRef

from api.pagination import CustomPagination
from resolve_crm.filters.sale_filter import SaleFilterSet
from resolve_crm.serializers.sale import SaleListSerializer

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from resolve_crm.models import Sale, Project, Attachment, ContractSubmission

class OptimizedSaleListViewSet(ReadOnlyModelViewSet):
    serializer_class = SaleListSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = SaleFilterSet
    ordering_fields = ['created_at', 'customer__complete_name', 'contract_number', 'status', 'signature_date', 'total_value', 'branch__name']

    def get_queryset(self):
        user = self.request.user

        projects_qs = Project.objects.select_related(
            'inspection__final_service_opinion'
        ).order_by('-created_at')

        attachments_under_analysis_qs = Attachment.objects.filter(
            content_type__model='sale',
            status="EA"
        )
        
        released_projects_subquery = Project.objects.with_is_released_to_engineering().filter(
            sale_id=OuterRef('pk'), 
            is_released_to_engineering=True
        )

        
        qs = Sale.objects.annotate(
            documents_under_analysis_count=Count('attachments', filter=Q(attachments__status='EA'))
        ).select_related(
            "customer", 
            "branch",
        ).prefetch_related(
            Prefetch(
                "contract_submissions",
                queryset=ContractSubmission.objects.order_by("-submit_datetime"),
                to_attr="all_submissions",
            ),
            Prefetch(
                "projects",
                queryset=projects_qs,
                to_attr="cached_projects"
            )
        )

        if not (user.is_superuser or user.has_perm("resolve_crm.view_all_sales")):
            stakeholder = Q(customer=user) | Q(seller=user)
            if hasattr(user, "employee"):
                branch_q = Q(branch__in=user.employee.related_branches.all())
                qs = qs.filter(stakeholder | branch_q)
            else:
                qs = qs.filter(stakeholder)
            
        return qs.distinct().order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        indicators = queryset.aggregate(
            pending_count=Count("id", filter=Q(status="P")),
            pending_total_value=Sum("total_value", filter=Q(status="P")),
            finalized_count=Count("id", filter=Q(status="F")),
            finalized_total_value=Sum("total_value", filter=Q(status="F")),
            in_progress_count=Count("id", filter=Q(status="EA")),
            in_progress_total_value=Sum("total_value", filter=Q(status="EA")),
            canceled_count=Count("id", filter=Q(status="C")),
            canceled_total_value=Sum("total_value", filter=Q(status="C")),
            terminated_count=Count("id", filter=Q(status="D")),
            terminated_total_value=Sum("total_value", filter=Q(status="D")),
            total_value_sum=Sum("total_value"),
        )

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            
            if 'meta' not in response.data:
                response.data['meta'] = {}
            response.data['meta']['indicators'] = indicators
            
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'meta': {'indicators': indicators}
        })