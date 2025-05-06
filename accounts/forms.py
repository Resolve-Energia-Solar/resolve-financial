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
        name_parts = complete_name.split()
        
        if not name_parts:
            raise ValueError("O nome completo não pode estar vazio.")

        user.first_name = name_parts[0]
        if len(name_parts) > 1:
            user.last_name = ' '.join(name_parts[1:])
        else:
            user.last_name = ''
            
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        user.password = make_password(password)
        if commit:
            user.save()
        return user
