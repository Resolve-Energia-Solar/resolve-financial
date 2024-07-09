from typing import Any, Mapping
from django.core.files.base import File
from django.db.models.base import Model
from django.forms import ModelForm, DateInput, TextInput
from django.forms.utils import ErrorList
from .models import User


class UserForm(ModelForm):
    class Meta:
        model = User
        exclude = ["last_login", "date_joined", "is_superuser", "is_staff", "is_active", "groups", "user_permissions", "password", "resignation_date"]
        widgets = {
            "hire_date": DateInput(attrs={'type': 'date'}),
            "birth_date": DateInput(attrs={'type': 'date'}),
        }


class UserUpdateForm(ModelForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        self.fields['address'].widget.attrs['value'] = instance.address.__str__()

    class Meta:
        model = User
        exclude = ["last_login", "date_joined", "is_superuser", "is_staff", "is_active", "groups", "user_permissions", "password"]
        widgets = {
            "hire_date": DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            "birth_date": DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            "resignation_date": DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            "address": TextInput(attrs={'type': 'hidden'}),
        }
