from rest_flex_fields import FlexFieldsModelSerializer
from django.apps import apps

class BaseSerializer(FlexFieldsModelSerializer):
    
    class Meta:
        model = None
        exclude = []
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove o campo 'is_deleted' se existir
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
            related_model = field.related_model
            serializer_name = f"{related_model.__name__}Serializer"
            serializer_path = f"{related_model._meta.app_label}.{serializer_name}"

            # Determina se o relacionamento é muitos (1-M ou M-M)
            is_many = field.one_to_many or field.many_to_many

            # Adiciona ao dicionário de campos expansíveis
            expandable_fields[field.name] = (serializer_path, {'many': is_many})
        
        return expandable_fields
    
    @property
    def expandable_fields(self):
        """
        Retorna os expandable_fields dinamicamente.
        """
        return self.get_expandable_fields()
