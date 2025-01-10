from api.views import BaseModelViewSet
from .models import *
from .serializers import *
from decimal import Decimal

class MaterialsViewSet(BaseModelViewSet):
    queryset = Materials.objects.all()
    serializer_class = MaterialsSerializer
    

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        query = super().get_queryset()
        kwp_in = self.request.query_params.get('kwp_in', None)
        
        if kwp_in:
            kwp_values = [Decimal(value) for value in kwp_in.split(',')]
            
            query = query.filter(
                materials__material__attributes__key='kwp',
                materials__material__attributes__value__in=kwp_values
            ).distinct()
        
        return query


    def perform_create(self, serializer):
        is_default = self.request.data.get('is_default', None)

        if is_default is not None and not bool(is_default):
            sale_id = self.request.data.get('sale_id', None)
            if not sale_id:
                raise serializers.ValidationError({"sale_id": "Este campo é obrigatório quando is_default é false."})
        
        serializer.save()
