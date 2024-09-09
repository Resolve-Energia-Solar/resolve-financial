from django.urls import path

from .views import *

app_name = 'logistics'
urlpatterns = [
    # Materials
    path('materiais/criar/', MaterialsCreateView.as_view(), name='materials_create'),
    path('materiais/', MaterialsListView.as_view(), name='materials_list'),
    path('materiais/<int:pk>/', MaterialsDetailView.as_view(), name='materials_detail'),
    path('materiais/<int:pk>/editar/', MaterialsUpdateView.as_view(), name='materials_update'),
    
    # Sales Materials
    path('materiais-vendas/criar/', SalesMaterialsCreateView.as_view(), name='sales_materials_create'),
    path('materiais-vendas/', SalesMaterialsListView.as_view(), name='sales_materials_list'),
    path('materiais-vendas/<int:pk>/', SalesMaterialsDetailView.as_view(), name='sales_materials_detail'),
    path('materiais-vendas/<int:pk>/editar/', SalesMaterialsUpdateView.as_view(), name='sales_materials_update'),
]