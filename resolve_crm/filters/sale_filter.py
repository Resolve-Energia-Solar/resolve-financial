# Em resolve_crm/filters.py

import django_filters
from django.db.models import Q
from ..models import Sale

class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass

class SaleFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filter_q', label="Busca Geral")

    delivery_type__in = NumberInFilter(field_name='projects__delivery_type', lookup_expr='in')
    final_service_options = NumberInFilter(field_name='projects__inspection__final_service_opinion__id', lookup_expr='in')
    borrower__in = NumberInFilter(field_name='payments__borrower__id', lookup_expr='in')
    
    invoice_status__in = django_filters.BaseInFilter(field_name='payments__invoice_status', lookup_expr='in')
    payments_types__in = django_filters.BaseInFilter(field_name='payments__payment_type', lookup_expr='in')

    is_signed = django_filters.BooleanFilter(method='filter_is_signed')
    documents_under_analysis = django_filters.BooleanFilter(method='filter_documents_under_analysis')

    tag_name__exact = django_filters.CharFilter(field_name='tags__tag', lookup_expr='exact')
    borrower = django_filters.NumberFilter(field_name='payments__borrower__id')
    homologator = django_filters.NumberFilter(field_name='projects__homologator__id')

    class Meta:
        model = Sale
        fields = {
            'status': ['exact', 'in'],
            'payment_status': ['exact', 'in'],
            'branch': ['exact', 'in'],
            'seller': ['exact', 'in'],
            'sales_supervisor': ['exact', 'in'],
            'sales_manager': ['exact', 'in'],
            'supplier': ['exact', 'in'],
            'is_pre_sale': ['exact'],
            'billing_date': ['exact', 'gte', 'lte', 'range'],
            'created_at': ['exact', 'gte', 'lte', 'range'],
        }

    def filter_q(self, queryset, name, value):
        if not value:
            return queryset
        
        return queryset.filter(
            Q(contract_number__icontains=value)
            | Q(customer__first_document__icontains=value)
            | Q(customer__complete_name__icontains=value)
            | Q(customer__email__icontains=value)
            | Q(projects__homologator__first_document__icontains=value)
            | Q(projects__homologator__complete_name__icontains=value)
            | Q(projects__homologator__email__icontains=value)
            | Q(seller__first_document__icontains=value)
            | Q(seller__complete_name__icontains=value)
            | Q(seller__email__icontains=value)
            | Q(sales_supervisor__first_document__icontains=value)
            | Q(sales_supervisor__complete_name__icontains=value)
            | Q(sales_supervisor__email__icontains=value)
            | Q(sales_manager__first_document__icontains=value)
            | Q(sales_manager__complete_name__icontains=value)
            | Q(sales_manager__email__icontains=value)
            | Q(supplier__first_document__icontains=value)
            | Q(supplier__complete_name__icontains=value)
            | Q(supplier__email__icontains=value)
            | Q(payments__borrower__first_document__icontains=value)
            | Q(payments__borrower__complete_name__icontains=value)
            | Q(payments__borrower__email__icontains=value)
        ).distinct()

    def filter_is_signed(self, queryset, name, value):
        if value is True:
            return queryset.filter(signature_date__isnull=False)
        if value is False:
            return queryset.filter(signature_date__isnull=True)
        return queryset

    def filter_documents_under_analysis(self, queryset, name, value):
        condition = Q(attachments__document_type__required=True, attachments__status="EA")
        if value is True:
            return queryset.filter(condition)
        if value is False:
            return queryset.exclude(condition)
        return queryset