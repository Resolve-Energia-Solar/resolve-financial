from django import forms
from django.contrib.auth.hashers import make_password
import random
import string
from .models import User 


class CustomUserCreationForm(forms.ModelForm):
    """Formulário de criação de usuário sem o campo de senha."""
    class Meta:
        model = User
        fields = ('email', 'complete_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        complete_name = self.cleaned_data['complete_name']
        if len(complete_name.split()) < 2:
            raise ValueError("O nome completo deve ter pelo menos dois nomes.")
        user.first_name = complete_name.split()[0]
        user.last_name = ' '.join(complete_name.split()[1:])
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        user.password = make_password(password)
        if commit:
            user.save()
        return user
