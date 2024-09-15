from .models import *
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from .forms import RequestsEnergyCompanyForm
from django.utils import timezone


class IndexView(TemplateView):
    template_name = 'engineering/index.html'
    

class EnergyCompanyView(UserPassesTestMixin, ListView):
    model = EnergyCompany
    template_name = 'engineering/energy_company/energy_company_list.html'
    ordering = ['name']
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.has_perm('engineering.view_energycompany')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        return queryset
    
class EnergyCompanyCreateView(UserPassesTestMixin, CreateView):
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
    
class EnergyCompanyUpdateView(UserPassesTestMixin, UpdateView):
    template_name = 'engineering/energy_company/energy_company_form.html'
    model = EnergyCompany
    fields = ['name', 'cnpj', 'address', 'phone', 'email']
    success_url = reverse_lazy('engineering:energycompany_list')
    
    def test_func(self):
        return self.request.user.has_perm('engineering.change_energycompany')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        
        return queryset.filter()
    
class RequestsEnergyCompanyView(UserPassesTestMixin, ListView):
    model = RequestsEnergyCompany
    template_name = 'engineering/requests_energy_company/requests_energy_company_list.html'
    ordering = ['-request_date']
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.has_perm('engineering.view_RequestsEnergyCompany')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        
        if 'search' in self.request.GET:
            search = self.request.GET['search']
            queryset = queryset.filter(company__name__icontains=search)
        
        return queryset
    
class RequestsEnergyCompanyCreateView(UserPassesTestMixin, CreateView):
    template_name = 'engineering/requests_energy_company/requests_energy_company_form.html'
    model = RequestsEnergyCompany
    form_class = RequestsEnergyCompanyForm
    success_url = reverse_lazy('engineering:requestsenergycompany_list')
    
    def form_valid(self, form):
        if form.instance.status == 'D' or form.instance.status == 'I':
            form.instance.conclusion_registred = timezone.now()
        messages.success(self.request, 'Solicitação de distribuidora de energia criada com sucesso!')
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.has_perm('engineering.add_RequestsEnergyCompany')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        
        return queryset.filter()
    
    
class RequestsEnergyCompanyUpdateView(UserPassesTestMixin, UpdateView):
    template_name = 'engineering/requests_energy_company/requests_energy_company_form.html'
    model = RequestsEnergyCompany
    form_class = RequestsEnergyCompanyForm
    success_url = reverse_lazy('engineering:requestsenergycompany_list')
    
    def form_valid(self, form):
        if form.instance.status == 'D' or form.instance.status == 'I':
            form.instance.conclusion_registred = timezone.now()
        messages.success(self.request, 'Solicitação de distribuidora de energia atualizada com sucesso!')
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.has_perm('engineering.change_RequestsEnergyCompany')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        
        return queryset.filter()
    

class RequestsEnergyCompanyDetailView(UserPassesTestMixin, DetailView):
    model = RequestsEnergyCompany
    template_name = 'engineering/requests_energy_company/requests_energy_company_detail.html'
    
    def test_func(self):
        return self.request.user.has_perm('engineering.view_RequestsEnergyCompany')

    
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
    

class CircuitBreakerCreateView(UserPassesTestMixin, CreateView):
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


class CircuitBreakerUpdateView(UserPassesTestMixin, UpdateView):
    template_name = 'engineering/circuit_breaker/circuit_breaker_form.html'
    model = CircuitBreaker
    fields = ['material', 'pole', 'current']
    success_url = reverse_lazy('engineering:circuitbreaker_list')
    
    def test_func(self):
        return self.request.user.has_perm('engineering.change_circuitbreaker')

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        
        return queryset.filter()