from django.views.generic import ListView, CreateView, UpdateView
from .models import RoofType
from django.urls import reverse_lazy


class RoofTypeCreateView(CreateView):
    model = RoofType
    fields = ['name']
    template_name = 'roof_types/roof_type_form.html'
    success_url = reverse_lazy('inspections:rooftype_list')
    
    
class RoofTypeListView(ListView):
    model = RoofType
    template_name = 'inspections/rooftype_list.html'
    
    
class RoofTypeUpdateView(UpdateView):
    model = RoofType
    fields = ['name']
    template_name = 'roof_types/roof_type_form.html'
    success_url = '/rooftype_list/'