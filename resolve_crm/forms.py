from django import forms
from .models import Squad, Task, Lead
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


class SquadForm(forms.ModelForm):
    class Meta:
        model = Squad
        fields = "__all__"
        widgets = {
            'branch': Select2Widget,
            'manager': Select2Widget,
            'members': Select2MultipleWidget,
            'boards': Select2MultipleWidget
        }