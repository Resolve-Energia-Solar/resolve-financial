from api.views import BaseModelViewSet
from .models import *
from .serializers import *
from .filters import PurchaseFilterSet
from django.db.models import Prefetch


class MaterialsViewSet(BaseModelViewSet):
    queryset = Materials.objects.all()
    serializer_class = MaterialsSerializer


class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_queryset(self):
        # Recupera a consulta inicial
        query = super().get_queryset()

        user = self.request.user

        if not user.is_superuser or not user.has_perm("logistics.view_all_products"):
            branch = user.employee.branch
            query = query.filter(branch=branch)

        # Aplica o filtro `kwp_in` se presente nos parâmetros da requisição
        kwp_in = self.request.query_params.get("kwp_in", None)
        if kwp_in:
            try:
                kwp_values = [float(value) for value in kwp_in.split(",")]
                if len(kwp_values) == 2:
                    query = query.filter(
                        params__gte=kwp_values[0], params__lte=kwp_values[1]
                    )
            except ValueError:
                query = query.none()
                pass

        return query.select_related("roof_type").prefetch_related(
            "materials",
            "branch",
            Prefetch(
                "product_material",
                queryset=ProductMaterials.objects.select_related("material"),
            ),
        )

    def filter_queryset(self, queryset):
        """
        Extende a lógica de filter_queryset para aplicar o ordering e outros filtros.
        """
        # Aplica os filtros normais e ordering
        queryset = super().filter_queryset(queryset)

        # Adicionalmente, aplica o filtro kwp_in
        kwp_in = self.request.query_params.get("kwp_in", None)
        if kwp_in:
            try:
                kwp_values = [float(value) for value in kwp_in.split(",")]
                if len(kwp_values) == 2:
                    queryset = queryset.filter(
                        params__gte=kwp_values[0], params__lte=kwp_values[1]
                    )
            except ValueError:
                # Ignore filtros malformados
                pass

        return queryset

    def perform_create(self, serializer):
        is_default = self.request.data.get("is_default", None)

        if is_default is not None and not bool(is_default):
            sale_id = self.request.data.get("sale_id", None)
            if not sale_id:
                raise serializers.ValidationError(
                    {"sale_id": "Este campo é obrigatório quando is_default é false."}
                )

        serializer.save()


class ProjectMaterialsViewSet(BaseModelViewSet):
    queryset = ProjectMaterials.objects.select_related('material').all()
    serializer_class = ProjectMaterialsSerializer


class SaleProductViewSet(BaseModelViewSet):
    queryset = SaleProduct.objects.all()
    serializer_class = SaleProductSerializer


class PurchaseViewSet(BaseModelViewSet):
    queryset = Purchase.objects.select_related(
        'project__sale__customer',
        'supplier'
    ).all()
    serializer_class = PurchaseSerializer
    filterset_class = PurchaseFilterSet
