import django_filters
from django.db.models import Q
from .models import Purchase


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class PurchaseFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filter_q', label="Busca Geral")
    
    # Filtros por cliente através da relação project -> sale -> customer
    customer = django_filters.NumberFilter(field_name='project__sale__customer__id', lookup_expr='exact', label="ID do Cliente")
    customer__in = django_filters.BaseInFilter(field_name='project__sale__customer__id', lookup_expr='in', label="IDs dos Clientes")
    customer_name = django_filters.CharFilter(field_name='project__sale__customer__complete_name', lookup_expr='icontains', label="Nome do Cliente")
    customer_document = django_filters.CharFilter(field_name='project__sale__customer__first_document', lookup_expr='icontains', label="Documento do Cliente")
    customer_email = django_filters.CharFilter(field_name='project__sale__customer__email', lookup_expr='icontains', label="Email do Cliente")
    
    # Filtros por projeto
    project = django_filters.NumberFilter(field_name='project__id', lookup_expr='exact', label="ID do Projeto")
    project__in = django_filters.BaseInFilter(field_name='project__id', lookup_expr='in', label="IDs dos Projetos")
    project_number = django_filters.CharFilter(field_name='project__project_number', lookup_expr='icontains', label="Número do Projeto")
    
    # Filtros por fornecedor
    supplier = django_filters.NumberFilter(field_name='supplier__id', lookup_expr='exact', label="ID do Fornecedor")
    supplier__in = django_filters.BaseInFilter(field_name='supplier__id', lookup_expr='in', label="IDs dos Fornecedores")
    supplier_name = django_filters.CharFilter(field_name='supplier__complete_name', lookup_expr='icontains', label="Nome do Fornecedor")
    supplier_document = django_filters.CharFilter(field_name='supplier__first_document', lookup_expr='icontains', label="Documento do Fornecedor")

    class Meta:
        model = Purchase
        fields = {
            'status': ['exact', 'in'],
            'purchase_date': ['exact', 'gte', 'lte', 'range'],
            'delivery_forecast': ['exact', 'gte', 'lte', 'range'],
            'purchase_value': ['exact', 'gte', 'lte'],
            'is_deleted': ['exact'],
        }

    def filter_q(self, queryset, name, value):
        if not value:
            return queryset
        
        return queryset.filter(
            Q(project__project_number__icontains=value)
            | Q(project__sale__customer__complete_name__icontains=value)
            | Q(project__sale__customer__first_document__icontains=value)
            | Q(project__sale__customer__email__icontains=value)
            | Q(project__sale__customer__phone__icontains=value)
            | Q(supplier__complete_name__icontains=value)
            | Q(supplier__first_document__icontains=value)
            | Q(supplier__email__icontains=value)
            | Q(supplier__phone__icontains=value)
            | Q(delivery_number__icontains=value)
        ).distinct()
