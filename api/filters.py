import django_filters
from django_filters.rest_framework import FilterSet
from django.apps import apps

class GenericFilter(FilterSet):
    def __init__(self, *args, **kwargs):
        model = kwargs.pop('model')
        self.Meta = type('Meta', (object,), {
            'model': model,
            'fields': '__all__' 
        })
        super(GenericFilter, self).__init__(*args, **kwargs)
