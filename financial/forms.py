from django import forms
from .models import PaymentRequest
from django_select2.forms import Select2Widget, HeavySelect2Widget


class PaymentRequestForm(forms.ModelForm):
    
    class Meta:
        model = PaymentRequest
        fields = '__all__'
        fields = ['causative_department', 'sale', 'supplier', 'description', 'category', 'amount', 'payment_method', 'service_date', 'invoice_number']
        labels = {
            'supplier': 'Beneficiário (CPF/CNPJ)'
        }
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'mask-money', 'type': 'text'}),
            'requester': Select2Widget(attrs={'data-placeholder': 'Selecionar solicitante'}),
            'manager': Select2Widget(attrs={'data-placeholder': 'Selecionar aprovador'}),
            'supplier': HeavySelect2Widget(data_view='financial:suppliers_list', attrs={'data-placeholder': 'Selecionar fornecedor', 'data-minimum-input-length': 11}),
            'category': HeavySelect2Widget(data_view='financial:categories_list', attrs={'data-placeholder': 'Selecionar categoria', 'data-minimum-input-length': 3}),
            'sale': Select2Widget(attrs={'data-placeholder': 'Selecionar venda', 'data-minimum-input-length': 3}),
            'service_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_method': Select2Widget(attrs={'data-placeholder': 'Selecionar forma de pagamento'}),
            'causative_department': Select2Widget(attrs={'data-placeholder': 'Selecionar departamento'}),
        }
