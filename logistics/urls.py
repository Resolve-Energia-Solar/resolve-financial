from api.urls import router
from logistics.views import *


router.register('materials', MaterialsViewSet, basename='material')
router.register('products', ProductViewSet, basename='product')
router.register('project-materials', ProjectMaterialsViewSet, basename='project-material')
router.register('sale-products', SaleProductViewSet, basename='sale-product')
router.register('purchase' , PurchaseViewSet, basename='purchase')
router.register('delivery-type', DeliveryTypeViewSet, basename='delivery-type')
