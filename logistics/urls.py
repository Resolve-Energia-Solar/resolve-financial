from django.urls import path

from .views import *

app_name = 'logistics'
urlpatterns = [
    # Materials
    path('materiais/criar/', MaterialsCreateView.as_view(), name='materials_create'),
    path('materiais/', MaterialsListView.as_view(), name='materials_list'),
    path('materiais/<int:pk>/', MaterialsDetailView.as_view(), name='materials_detail'),
    path('materiais/<int:pk>  /editar/', MaterialsUpdateView.as_view(), name='materials_update'),
    # Material Types
    path('tipos-de-materiais/criar/', MaterialTypesCreateView.as_view(), name='material_type_create'),
    path('tipos-de-materiais/', MaterialTypesListView.as_view(), name='material_type_list'),
    path('tipos-de-materiais/<int:pk>/', MaterialTypesDetailView.as_view(), name='material_type_detail'),
    path('tipos-de-materiais/<int:pk>/editar/', MaterialTypesUpdateView.as_view(), name='material_type_update'),
    # Sales Materials
    path('materiais-vendas/criar/', SalesMaterialsCreateView.as_view(), name='sales_materials_create'),
    path('materiais-vendas/', SalesMaterialsListView.as_view(), name='sales_materials_list'),
    path('materiais-vendas/<int:pk>/', SalesMaterialsDetailView.as_view(), name='sales_materials_detail'),
    path('materiais-vendas/<int:pk>/editar/', SalesMaterialsUpdateView.as_view(), name='sales_materials_update'),
    # Solar Energy Kit 
]