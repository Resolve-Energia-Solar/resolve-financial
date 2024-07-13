from django import forms
from .models import Task, Lead
from django_select2.forms import Select2Widget, Select2MultipleWidget


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
            'address': Select2Widget,
            'seller': Select2Widget,
            'squad': Select2Widget,
            'responsible': Select2Widget
        }