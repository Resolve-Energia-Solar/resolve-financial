from .models import CircuitBreaker
from django.views.generic import TemplateView, CreateView, ListView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin


class IndexView(TemplateView):
    template_name = 'engineering/index.html'

    
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