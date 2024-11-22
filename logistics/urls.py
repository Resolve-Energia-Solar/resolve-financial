from api.urls import router
from logistics.views import *


router.register('materials', MaterialsViewSet, basename='material')
router.register('products', ProductViewSet, basename='product')
