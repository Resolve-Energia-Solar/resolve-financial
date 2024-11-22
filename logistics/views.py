from requests import Response

from api.views import BaseModelViewSet
from .models import *
from .serializers import *


class MaterialsViewSet(BaseModelViewSet):
    queryset = Materials.objects.all()
    serializer_class = MaterialsSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        material = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def perform_create(self, serializer):
        is_default = self.request.data.get('is_default', None)

        # Verifica se `is_default` é `false`
        if is_default is not None and not bool(is_default):
            sale_id = self.request.data.get('sale_id', None)
            if not sale_id:
                raise serializers.ValidationError({"sale_id": "Este campo é obrigatório quando is_default é false."})
        
        # Salva o objeto usando o serializer
        serializer.save()
