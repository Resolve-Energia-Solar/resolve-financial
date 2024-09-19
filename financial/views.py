from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from .models import PaymentRequest


class PaymentRequestListView(UserPassesTestMixin, ListView):
    model = PaymentRequest
    template_name = 'financial/payment_requests_list.html'
    context_object_name = 'payment_requests'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.has_perm('financial.view_paymentrequest')
    
    def get_queryset(self):
        return PaymentRequest.objects.filter(requester=self.request.user) | PaymentRequest.objects.filter(manager=self.request.user) | PaymentRequest.objects.filter(deparment=self.request.user) | PaymentRequest.objects.filter(supplier=self.request.user)
    

class PaymentRequestDetailView(UserPassesTestMixin, DetailView):
    
    model = PaymentRequest
    template_name = 'financial/payment_requests_detail.html'
    
    def test_func(self):
        return self.request.user.has_perm('financial.view_paymentrequest') or self.request.user == self.get_object().requester or self.request.user == self.get_object().manager or self.request.user == self.get_object().deparment or self.request.user == self.get_object().supplier
    

class PaymentRequestCreateView(UserPassesTestMixin, CreateView):
        
        model = PaymentRequest
        template_name = 'financial/payment_requests_form.html'
        fields = '__all__'
        success_url = reverse_lazy('financial:payment_requests_list')
        
        def test_func(self):
            return self.request.user.has_perm('financial.add_paymentrequest')


class PaymentRequestUpdateView(UserPassesTestMixin, UpdateView):
    
    model = PaymentRequest
    template_name = 'financial/payment_requests_form.html'
    fields = '__all__'
    success_url = reverse_lazy('financial:payment_requests_list')
    
    def test_func(self):
        return self.request.user.has_perm('financial.change_paymentrequest')
