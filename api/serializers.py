from rest_flex_fields import FlexFieldsModelSerializer


class BaseSerializer(FlexFieldsModelSerializer):
    
    class Meta:
        model = None
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'is_deleted' in self.fields:
            self.fields.pop('is_deleted')
            
    def get_expandable_fields(self):
        """
        Retorna campos expansíveis dinamicamente com base nos relacionamentos do modelo.
        """
        expandable_fields = {}
        related_fields = [
            field for field in self.Meta.model._meta.get_fields()
            if field.is_relation and field.related_model is not None
        ]
        for field in related_fields:
            serializer_name = f"{field.related_model.__name__}Serializer"
            field_config = {
                'many': field.one_to_many or field.many_to_many  # Define `many` dinamicamente
            }
            expandable_fields[field.name] = (
                f"{field.related_model._meta.app_label}.{serializer_name}",
                field_config
            )
        return expandable_fields

    @property
    def expandable_fields(self):
        """
        Retorna os expandable_fields dinamicamente.
        """
        return self.get_expandable_fields()