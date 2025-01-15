from rest_flex_fields import FlexFieldsModelSerializer
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

class BaseSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = None
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'is_deleted' in self.fields:
            self.fields.pop('is_deleted')

    @cached_property
    def get_expandable_fields(self):
        expandable_fields = {}
        related_fields = [
            f for f in self.Meta.model._meta.get_fields()
            if f.is_relation and f.related_model
        ]
        for field in related_fields:
            related_model = field.related_model
            if related_model == ContentType:
                # Use o seu ContentTypeSerializer específico
                serializer_path = 'accounts.serializers.ContentTypeSerializer'
            else:
                # Gera o path normalmente
                serializer_name = f"{related_model.__name__}Serializer"
                serializer_path = f"{related_model._meta.app_label}.{serializer_name}"

            is_many = field.one_to_many or field.many_to_many
            expandable_fields[field.name] = (serializer_path, {'many': is_many})
        return expandable_fields

    @property
    def expandable_fields(self):
        return self.get_expandable_fields
