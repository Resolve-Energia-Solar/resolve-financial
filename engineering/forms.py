from django.contrib.auth.models import Group
from django.forms import ModelForm, DateInput
from .models import *
from django_select2.forms import Select2MultipleWidget, Select2Widget, ModelSelect2MultipleWidget


class RequestsEnergyCompanyForm(ModelForm):
    class Meta:
        model = RequestsEnergyCompany
        exclude = ['is_deleted', 'conclusion_registred']
        widgets = {
            'company': Select2Widget,
            'project': Select2Widget,
            'request_date': DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'status': Select2Widget,
            'conclusion_date': DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

