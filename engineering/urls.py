from django.urls import path
from .views import *

app_name = 'engineering'

urlpatterns = [
    path('', IndexView.as_view(), name='engenharia'),
    
    #Disjuntores
    path('disjuntores/', CircuitBreakerView.as_view(), name='circuitbreaker_list'),
    path('disjuntores/novo/', CircuitBreakerCreateView.as_view(), name='circuitbreaker_create'),
    path('disjuntores/editar/<int:pk>/', CircuitBreakerUpdateView.as_view(), name='circuitbreaker_update'),
    
    #Concessionárias de Energia
    path('concessionarias/', EnergyCompanyView.as_view(), name='energycompany_list'),
    path('concessionarias/novo/', EnergyCompanyCreateView.as_view(), name='energycompany_create'),
    path('concessionarias/editar/<int:pk>/', EnergyCompanyUpdateView.as_view(), name='energycompany_update'),
    
    #Solicitações de Concessionárias de Energia
    path('solicitacoes/', RequestsEnergyCompanyView.as_view(), name='requestsenergycompany_list'),
    path('solicitacoes/novo/', RequestsEnergyCompanyCreateView.as_view(), name='requestsenergycompany_create'),
    path('solicitacoes/editar/<int:pk>/', RequestsEnergyCompanyUpdateView.as_view(), name='requestsenergycompany_update'),
    path('solicitacoes/detalhes/<int:pk>/', RequestsEnergyCompanyDetailView.as_view(), name='requestsenergycompany_detail'),
    
]