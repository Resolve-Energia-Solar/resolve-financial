from rest_framework import serializers


class DynamicSerializerMixin:
    @classmethod
    def get_dynamic_serializer(cls, model_query, fields_query):
        class DynamicSerializer(serializers.ModelSerializer):
            class Meta:
                model = model_query
                fields = fields_query

        return DynamicSerializer
    