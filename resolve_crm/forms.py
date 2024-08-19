from django import forms

from .models import Task, Lead, MarketingCampaign
from django_select2.forms import Select2Widget, Select2MultipleWidget, ModelSelect2Widget


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = "__all__"
        widgets = {
            'lead': Select2Widget,
            'description': forms.Textarea(attrs={'rows': 2}),
            'members': Select2MultipleWidget
        }


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = "__all__"
        widgets = {
            'address': ModelSelect2Widget(
                attrs={'data-placeholder': 'Selecionar endereço'},
                search_fields=[
                    'zip_code__icontains',
                    'country__icontains',
                    'state__icontains',
                    'city__icontains',
                    'neighborhood__icontains',
                    'street__icontains',
                    'number__icontains',
                    'complement__icontains',
                ]
            ),
            'seller': Select2Widget,
            'responsible': Select2Widget
        }


class MarketingCampaignForm(forms.ModelForm):
    class Meta:
        model = MarketingCampaign
        fields = "__all__"
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')
        }
        
    @property
    def has_file_field(self):
        return any(isinstance(field, forms.FileField) for field in self.fields.values())