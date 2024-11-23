from rest_framework.serializers import ModelSerializer


class BaseSerializer(ModelSerializer):
    
    class Meta:
        model = None
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'is_deleted' in self.fields:
            self.fields.pop('is_deleted')
