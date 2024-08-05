from django.contrib.auth.models import Group
from django.forms import ModelForm, DateInput
from .models import Branch, User, Squad
from django_select2.forms import Select2MultipleWidget, Select2Widget, ModelSelect2Widget


class UserForm(ModelForm):
    class Meta:
        model = User
        exclude = ["last_login", "date_joined", "is_superuser", "is_staff", "is_active", "password", "resignation_date"]
        widgets = {
            "hire_date": DateInput(attrs={'type': 'date'}),
            "birth_date": DateInput(attrs={'type': 'date'}),
            'branch': Select2Widget(attrs={'data-placeholder': 'Selecionar unidade'}),
            'department': Select2Widget(attrs={'data-placeholder': 'Selecionar departamento'}),
            'role': Select2Widget(attrs={'data-placeholder': 'Selecionar cargo'}),
            'user_manager': Select2Widget(attrs={'data-placeholder': 'Selecionar gestor'}),
            'user_permissions': Select2MultipleWidget(attrs={'data-placeholder': 'Selecionar permissões'}),
            'groups': Select2MultipleWidget(attrs={'data-placeholder': 'Selecionar perfis'}),
            'address': ModelSelect2Widget(attrs={'data-placeholder': 'Selecionar endereço'}, search_fields=[
                'zip_code__icontains',
                'country__icontains',
                'state__icontains',
                'city__icontains',
                'neighborhood__icontains',
                'street__icontains',
                'number__icontains',
                'complement__icontains',
            ])
        }


class UserUpdateForm(ModelForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        self.fields['address'].widget.attrs['value'] = instance.address.__str__()

    class Meta:
        model = User
        exclude = ["last_login", "date_joined", "is_superuser", "is_staff", "is_active", "password"]
        widgets = {
            "hire_date": DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            "birth_date": DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            "resignation_date": DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'branch': Select2Widget(attrs={'data-placeholder': 'Selecionar unidade'}),
            'department': Select2Widget(attrs={'data-placeholder': 'Selecionar departamento'}),
            'role': Select2Widget(attrs={'data-placeholder': 'Selecionar cargo'}),
            'user_manager': Select2Widget(attrs={'data-placeholder': 'Selecionar gestor'}),
            'user_permissions': Select2MultipleWidget(attrs={'data-placeholder': 'Selecionar permissões'}),
            'groups': Select2MultipleWidget(attrs={'data-placeholder': 'Selecionar perfis'}),
            'address': ModelSelect2Widget(attrs={'data-placeholder': 'Selecionar endereço'}, search_fields=[
                'zip_code__icontains',
                'country__icontains',
                'state__icontains',
                'city__icontains',
                'neighborhood__icontains',
                'street__icontains',
                'number__icontains',
                'complement__icontains',
            ])
        }


class GroupForm(ModelForm):
    class Meta:
        model = Group
        fields = '__all__'
        widgets = {
            'permissions': Select2MultipleWidget(attrs={'data-placeholder': 'Selecionar permissões'})
        }


class BranchForm(ModelForm):
    class Meta:
        model = Branch
        fields = '__all__'
        widgets = {
            'owners': Select2MultipleWidget(attrs={'data-placeholder': 'Selecionar proprietários'})
        }


class SquadForm(ModelForm):
    class Meta:
        model = Squad
        fields = "__all__"
        widgets = {
            'branch': Select2Widget,
            'manager': Select2Widget,
            'members': Select2MultipleWidget,
            'boards': Select2MultipleWidget
        }