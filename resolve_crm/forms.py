from django import forms

from .models import Task, Lead, MarketingCampaign
from django_select2.forms import Select2Widget, Select2MultipleWidget, ModelSelect2MultipleWidget
from django.core.exceptions import FieldDoesNotExist

class FormBase(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            try:
                related_model = field.queryset.model
                if hasattr(related_model, 'is_deleted'):
                    field.queryset = related_model.objects.filter(is_deleted=False)
            except AttributeError:
                continue

    class Meta:
        exclude = ['is_deleted']

class TaskForm(FormBase):
    class Meta:
        model = Task
        fields = "__all__"
        widgets = {
            'lead': Select2Widget,
            'description': forms.Textarea(attrs={'rows': 2}),
            'members': Select2MultipleWidget
        }


class LeadForm(FormBase):
    class Meta:
        model = Lead
        fields = "__all__"
        exclude = ['created_by', 'created_at', 'updated_by', 'updated_at', 'customer']
        widgets = {
            'addresses': ModelSelect2MultipleWidget(
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
            'seller': Select2Widget(attrs={'data-placeholder': 'Selecionar vendedor'}),
            'sdr': Select2Widget(attrs={'data-placeholder': 'Selecionar SDR'})
        }


class MarketingCampaignForm(FormBase):
    class Meta:
        model = MarketingCampaign
        exclude = ['is_deleted']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')
        }
        
    @property
    def has_file_field(self):
        return any(isinstance(field, forms.FileField) for field in self.fields.values())