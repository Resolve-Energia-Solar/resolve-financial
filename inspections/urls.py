from django.urls import path
from .views import RoofTypeListView

app_name = 'inspections'
urlpatterns = [
    path('tipos-de-telhado/criar/', RoofTypeListView.as_view(), name='rooftype_list'),
    path('tipos-de-telhado/<int:pk>/', RoofTypeListView.as_view(), name='rooftype_list'),
    path('tipos-de-telhado/', RoofTypeListView.as_view(), name='rooftype_list'),
]
