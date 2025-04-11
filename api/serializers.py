from rest_flex_fields import FlexFieldsModelSerializer
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

class BaseSerializer(FlexFieldsModelSerializer, ModelSerializer):
    str = serializers.SerializerMethodField()
    class Meta:
        model = None

    @cached_property
    def expandable_fields(self):
        model = self.Meta.model
        expandable = {}
        if not model:
            return expandable

        for field in model._meta.get_fields():
            if field.is_relation and field.related_model:
                related_model = field.related_model
                if related_model == ContentType:
                    serializer_path = 'accounts.serializers.ContentTypeSerializer'
                else:
                    serializer_name = f"{related_model.__name__}Serializer"
                    serializer_path = f"{related_model._meta.app_label}.{serializer_name}"
                is_many = field.many_to_many or field.one_to_many
                expandable[field.name] = (serializer_path, {'many': is_many})
        return expandable
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request')
        if request:
            requested_fields = request.query_params.get('fields', '')
            requested_fields = requested_fields.split(',')
            if 'str' not in requested_fields:
                self.fields.pop('str', None)
        else:
            self.fields.pop('str', None)

    def get_str(self, obj):
        return str(obj)
