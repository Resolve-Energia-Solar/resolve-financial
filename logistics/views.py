from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.contrib.auth.mixins import UserPassesTestMixin
from .models import Materials, SalesMaterials, MaterialTypes, SolarEnergyKit
from django.urls import reverse_lazy


class MaterialsCreateView(UserPassesTestMixin, CreateView):
    model = Materials
    fields = '__all__'
    template_name = 'logistics/materials/materials_form.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.add_materials')
    
    def get_success_url(self):
        return reverse_lazy('logistics:materials_detail', kwargs={'pk': self.object.pk})
    
    
class MaterialsListView(UserPassesTestMixin, ListView):
    model = Materials
    template_name = 'logistics/materials/materials_list.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.view_materials')


class MaterialsDetailView(UserPassesTestMixin, DetailView):
    model = Materials
    template_name = 'logistics/materials/materials_detail.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.view_materials')

    
class MaterialsUpdateView(UserPassesTestMixin, UpdateView):
    model = Materials
    fields = '__all__'
    template_name = 'logistics/materials/materials_form.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.change_materials')
    
    def get_success_url(self):
        return reverse_lazy('logistics:materials_detail', kwargs={'pk': self.object.pk})
    
    
class SalesMaterialsCreateView(UserPassesTestMixin, CreateView):
    model = SalesMaterials
    fields = '__all__'
    template_name = 'logistics/sales_materials_form.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.add_salesmaterials')
    
    def get_success_url(self):
        return reverse_lazy('logistics:sales_materials_detail', kwargs={'pk': self.object.pk})
    
    
class SalesMaterialsListView(UserPassesTestMixin, ListView):
    model = SalesMaterials
    template_name = 'logistics/sales_materials_list.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.view_salesmaterials')


class SalesMaterialsDetailView(UserPassesTestMixin, DetailView):
    model = SalesMaterials
    template_name = 'logistics/sales_materials_detail.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.view_salesmaterials')
    
    
class  SalesMaterialsUpdateView(UserPassesTestMixin, UpdateView):
    model = SalesMaterials
    fields = '__all__'
    template_name = 'logistics/sales_materials_form.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.view_salesmaterials')
    
    def get_success_url(self):
        return reverse_lazy('logistics:sales_materials_detail', kwargs={'pk': self.object.pk})


class MaterialTypesCreateView(UserPassesTestMixin, CreateView):
    model = MaterialTypes
    fields = ['name', 'description']
    template_name = 'logistics/material_types/material_type_form.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.add_materialtypes')
    
    def get_success_url(self):
        return reverse_lazy('logistics:material_type_list')
    
    
class MaterialTypesListView(UserPassesTestMixin, ListView):
    model = MaterialTypes
    template_name = 'logistics/material_types/material_type_list.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.view_materialtypes')
    
    
class MaterialTypesDetailView(UserPassesTestMixin, DetailView):
    model = MaterialTypes
    template_name = 'logistics/material_types/material_type_list.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.view_materialtypes')
    
    
class MaterialTypesUpdateView(UserPassesTestMixin, UpdateView):
    model = MaterialTypes
    fields = ['name', 'description']
    template_name = 'logistics/material_types/material_type_form.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.change_materialtypes')
    
    def get_success_url(self):
        return reverse_lazy('logistics:material_type_list')


class SolarEnergyKitCreateView(UserPassesTestMixin, CreateView):
    model = SolarEnergyKit
    fields = '__all__'
    template_name = 'logistics/solar_energy_kit_form.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.add_solarenergykit')
    
    def get_success_url(self):
        return reverse_lazy('logistics:solar_energy_kit_detail', kwargs={'pk': self.object.pk})
    
    
class SolarEnergyKitListView(UserPassesTestMixin, ListView):
    model = SolarEnergyKit
    template_name = 'logistics/solar_energy_kit_list.html'
    
    def test_func(self):
        return self.request.user.has_perm('logistics.view_solarenergykit')
    
    
class SolarEnergyKitDetailView(UserPassesTestMixin, DetailView):
    model = SolarEnergyKit
    template_name = 'logistics/solar_energy_kit_detail.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.view_solarenergykit')
    
    
class SolarEnergyKitUpdateView(UserPassesTestMixin, UpdateView):
    model = SolarEnergyKit
    fields = '__all__'
    template_name = 'logistics/solar_energy_kit_form.html'

    def test_func(self):
        return self.request.user.has_perm('logistics.change_solarenergykit')
    
    def get_success_url(self):
        return reverse_lazy('logistics:solar_energy_kit_detail', kwargs={'pk': self.object.pk})