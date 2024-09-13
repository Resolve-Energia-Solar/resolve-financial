from django.urls import path
from .views import *

app_name = 'engineering'

urlpatterns = [
    path('', IndexView.as_view(), name='engenharia'),
    
    #Disjuntores
    path('disjuntores/', CircuitBreakerView.as_view(), name='circuitbreaker_list'),
    path('disjuntores/novo/', CircuitBreakerCreateView.as_view(), name='circuitbreaker_create'),
    path('disjuntores/editar/<int:pk>/', CircuitBreakerUpdateView.as_view(), name='circuitbreaker_update'),
    
]