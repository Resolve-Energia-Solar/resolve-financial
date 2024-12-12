from api.views import BaseModelViewSet
from .models import *
from .serializers import *


class MaterialsViewSet(BaseModelViewSet):
    queryset = Materials.objects.all()
    serializer_class = MaterialsSerializer
    

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def perform_create(self, serializer):
        is_default = self.request.data.get('is_default', None)

        if is_default is not None and not bool(is_default):
            sale_id = self.request.data.get('sale_id', None)
            if not sale_id:
                raise serializers.ValidationError({"sale_id": "Este campo é obrigatório quando is_default é false."})
        
        serializer.save()
