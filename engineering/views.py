from .models import *
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from .forms import RequestEnergyCompanyForm


class IndexView(TemplateView):
    template_name = 'engineering/index.html'
    

class EnergyCompanyView(ListView):
    model = EnergyCompany
    template_name = 'engineering/energy_company/energy_company_list.html'
    ordering = ['name']
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.has_perm('engineering.view_energycompany')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        return queryset
    
class EnergyCompanyCreateView(CreateView):
    template_name = 'engineering/energy_company/energy_company_form.html'
    model = EnergyCompany
    fields = ['name', 'cnpj', 'address', 'phone', 'email']
    success_url = reverse_lazy('engineering:energycompany_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Distribuidora de energia criada com sucesso!')
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.has_perm('engineering.add_energycompany')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        
        return queryset.filter()
    
class EnergyCompanyUpdateView(UpdateView):
    template_name = 'engineering/energy_company/energy_company_form.html'
    model = EnergyCompany
    fields = ['name', 'cnpj', 'address', 'phone', 'email']
    success_url = reverse_lazy('engineering:energycompany_list')
    
    def test_func(self):
        return self.request.user.has_perm('engineering.change_energycompany')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        
        return queryset.filter()
    
class RequestsEnergyCompanyView(ListView):
    model = RequestsEnergyCompany
    template_name = 'engineering/requests_energy_company/requests_energy_company_list.html'
    ordering = ['-request_date']
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.has_perm('engineering.view_requestsenergycompany')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        return queryset
    
class RequestsEnergyCompanyCreateView(CreateView):
    template_name = 'engineering/requests_energy_company/requests_energy_company_form.html'
    model = RequestsEnergyCompany
    form_class = RequestEnergyCompanyForm
    success_url = reverse_lazy('engineering:requestsenergycompany_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Solicitação de distribuidora de energia criada com sucesso!')
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.has_perm('engineering.add_requestsenergycompany')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        
        return queryset.filter()
    
    
class RequestsEnergyCompanyUpdateView(UpdateView):
    template_name = 'engineering/requests_energy_company/requests_energy_company_form.html'
    model = RequestsEnergyCompany
    form_class = RequestEnergyCompanyForm
    success_url = reverse_lazy('engineering:requestsenergycompany_list')
    
    def test_func(self):
        return self.request.user.has_perm('engineering.change_requestsenergycompany')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        
        return queryset.filter()
    

class RequestsEnergyCompanyDetailView(DetailView):
    model = RequestsEnergyCompany
    template_name = 'engineering/requests_energy_company/requests_energy_company_detail.html'
    
    def test_func(self):
        return self.request.user.has_perm('engineering.view_requestsenergycompany')

    
class CircuitBreakerView(ListView):
    model = CircuitBreaker
    template_name = 'engineering/circuit_breaker/circuit_breaker_list.html'
    ordering = ['pole']
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.has_perm('engineering.view_circuitbreaker')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        return queryset
    

class CircuitBreakerCreateView(CreateView):
    template_name = 'engineering/circuit_breaker/circuit_breaker_form.html'
    model = CircuitBreaker
    fields = ['material', 'pole', 'current']
    success_url = reverse_lazy('engineering:circuitbreaker_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Disjuntor criado com sucesso!')
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.has_perm('engineering.add_circuitbreaker')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        
        return queryset.filter()


class CircuitBreakerUpdateView(UpdateView):
    template_name = 'engineering/circuit_breaker/circuit_breaker_form.html'
    model = CircuitBreaker
    fields = ['material', 'pole', 'current']
    success_url = reverse_lazy('engineering:circuitbreaker_list')
    
    def test_func(self):
        return self.request.user.has_perm('engineering.change_circuitbreaker')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        
        return queryset.filter()