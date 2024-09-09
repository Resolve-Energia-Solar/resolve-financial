from django.views.generic import CreateView, ListView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin
from .models import Materials, SalesMaterials
from django.urls import reverse_lazy


class MaterialsCreateView(UserPassesTestMixin, CreateView):
    model = Materials
    fields = '__all__'
    template_name = 'logistics/materials_create.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.add_materials')
    
    def get_success_url(self):
        return reverse_lazy('logistics:materials_detail', kwargs={'pk': self.object.pk})
    
    
class MaterialsListView(UserPassesTestMixin, ListView):
    model = Materials
    template_name = 'logistics/materials_list.html'
    context_object_name = 'materials'

    def test_func(self):
        return self.request.user.has_perm('logistics.view_materials')


class MaterialsDetailView(UserPassesTestMixin, ListView):
    model = Materials
    template_name = 'logistics/materials_detail.html'
    context_object_name = 'materials'

    def test_func(self):
        return self.request.user.has_perm('logistics.view_materials')
    
    
class MaterialsUpdateView(UserPassesTestMixin, UpdateView):
    model = Materials
    fields = '__all__'
    template_name = 'logistics/materials_update.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.change_materials')
    
    def get_success_url(self):
        return reverse_lazy('logistics:materials_detail', kwargs={'pk': self.object.pk})
    
    
class SalesMaterialsCreateView(UserPassesTestMixin, CreateView):
    model = SalesMaterials
    fields = '__all__'
    template_name = 'logistics/sales_materials_create.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.add_salesmaterials')
    
    def get_success_url(self):
        return reverse_lazy('logistics:sales_materials_detail', kwargs={'pk': self.object.pk})
    
    
class SalesMaterialsListView(UserPassesTestMixin, ListView):
    model = SalesMaterials
    template_name = 'logistics/sales_materials_list.html'
    context_object_name = 'sales_materials'

    def test_func(self):
        return self.request.user.has_perm('logistics.view_salesmaterials')


class SalesMaterialsDetailView(UserPassesTestMixin, ListView):
    model = SalesMaterials
    template_name = 'logistics/sales_materials_detail.html'
    context_object_name = 'sales_materials'

    def test_func(self):
        return self.request.user.has_perm('logistics.view_salesmaterials')
    
    
class SalesMaterialsUpdateView(UserPassesTestMixin, UpdateView):
    model = SalesMaterials
    fields = '__all__'
    template_name = 'logistics/sales_materials_update.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.view_salesmaterials')
    
    def get_success_url(self):
        return reverse_lazy('logistics:sales_materials_detail', kwargs={'pk': self.object.pk})
