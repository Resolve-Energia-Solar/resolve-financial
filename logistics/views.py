from api.views import BaseModelViewSet
from .models import *
from .serializers import *


class MaterialsViewSet(BaseModelViewSet):
    queryset = Materials.objects.all()
    serializer_class = MaterialsSerializer
    

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        query = super().get_queryset()
        user = self.request.user
        
        if not user.is_superuser or not user.has_perm('logistics.view_all_products'):
            branch = user.employee.branch
            query = query.filter(branch=branch)
            
            kwp_in = self.request.query_params.get('kwp_in', None)
            if kwp_in:
                kwp_values = kwp_in.split(',')
                
                query = query.filter(
                    params__gte=kwp_values[0],
                    params__lte=kwp_values[1]
                ).distinct()
        
        return query


    def perform_create(self, serializer):
        is_default = self.request.data.get('is_default', None)

        if is_default is not None and not bool(is_default):
            sale_id = self.request.data.get('sale_id', None)
            if not sale_id:
                raise serializers.ValidationError({"sale_id": "Este campo é obrigatório quando is_default é false."})
        
        serializer.save()
