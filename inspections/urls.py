from django.urls import path
from .views import RoofTypeListView, RoofTypeCreateView, RoofTypeUpdateView

app_name = 'inspections'
urlpatterns = [
    path('tipos-de-telhado/criar/', RoofTypeCreateView.as_view(), name='roof_type_create'),
    path('tipos-de-telhado/', RoofTypeListView.as_view(), name='roof_type_list'),
    path('tipos-de-telhado/<int:pk>/editar/', RoofTypeUpdateView.as_view(), name='roof_type_update')
]
