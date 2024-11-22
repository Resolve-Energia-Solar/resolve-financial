from requests import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter


class BaseModelViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = '__all__'
    http_method_names = ['get', 'post', 'put', 'delete', 'patch']

    def list(self, request, *args, **kwargs):
        fields = request.query_params.get('fields')
        
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.paginate_queryset(queryset)

        if fields:
            fields = fields.split(',')
            serializer = self.get_serializer(queryset, many=True)
            filtered_data = [
                {field: self._get_field_data(item, field) for field in fields}
                for item in serializer.data
            ]
            return self.get_paginated_response(filtered_data)

        serializer = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        fields = request.query_params.get('fields')
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        if fields:
            fields = fields.split(',')
            filtered_data = {field: self._get_field_data(serializer.data, field) for field in fields}
            return Response(filtered_data, status=status.HTTP_200_OK)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_field_data(self, obj, field):
        """Método auxiliar para obter dados de campos aninhados."""
        if '.' in field:
            keys = field.split('.')
            value = obj
            for key in keys:
                if isinstance(value, list):
                    value = [item.get(key, None) for item in value if isinstance(item, dict)]
                elif isinstance(value, dict):
                    value = value.get(key, None)
                else:
                    return None
            return value
        return obj.get(field, None)

    @property
    def filterset_fields(self):
        model = self.get_queryset().model
        exclude_field_types = ['ImageField', 'FileField']
        supported_lookups = ['CharField', 'TextField', 'ForeignKey', 'DateField', 'DateTimeField', 'PositiveSmallIntegerField', 'IntegerField', 'DecimalField', 'ManyToManyField', 'BooleanField']
    
        filter_fields = {}
        for field in model._meta.fields + model._meta.many_to_many:
            if field.get_internal_type() in supported_lookups and field.get_internal_type() not in exclude_field_types:
                if field.get_internal_type() in ['ForeignKey', 'BooleanField']:
                    filter_fields[field.name] = ['exact']
                elif field.get_internal_type() in ['CharField', 'TextField']:
                    filter_fields[field.name] = ['icontains', 'in']
                elif field.get_internal_type() in ['DateField', 'DateTimeField']:
                    filter_fields[field.name] = ['range']
                elif field.get_internal_type() in ['PositiveSmallIntegerField', 'IntegerField', 'DecimalField']:
                    filter_fields[field.name] = ['exact', 'gte', 'lte']
                elif field.get_internal_type() == 'ManyToManyField':
                    filter_fields[field.name] = ['exact', 'in']
        return filter_fields
