from django import forms
from .models import PaymentRequest
from django_select2.forms import Select2Widget, HeavySelect2Widget


class PaymentRequestForm(forms.ModelForm):
    
    supplier_name = forms.CharField(widget=forms.HiddenInput(), required=False)
    supplier_cpf = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = PaymentRequest
        fields = '__all__'
        fields = ['causative_department', 'sale', 'supplier', 'description', 'category', 'amount', 'payment_method', 'service_date', 'due_date', 'invoice_number', 'supplier_name', 'supplier_cpf']
        labels = {
            'supplier': 'Beneficiário (CPF/CNPJ)'
        }
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'mask-money', 'type': 'text'}),
            'requester': Select2Widget(attrs={'data-placeholder': 'Selecionar solicitante'}),
            'manager': Select2Widget(attrs={'data-placeholder': 'Selecionar aprovador'}),
            'supplier': HeavySelect2Widget(data_view='financial:suppliers_list', attrs={'data-placeholder': 'Selecionar fornecedor', 'data-minimum-input-length': 11, 'data-ajax--delay': 1000}),
            'category': HeavySelect2Widget(data_view='financial:categories_list', attrs={'data-placeholder': 'Selecionar categoria', 'data-minimum-input-length': 3, 'data-ajax--delay': 1000}),
            'sale': Select2Widget(attrs={'data-placeholder': 'Selecionar venda', 'data-minimum-input-length': 3}),
            'service_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_method': Select2Widget(attrs={'data-placeholder': 'Selecionar forma de pagamento'}),
            'causative_department': Select2Widget(attrs={'data-placeholder': 'Selecionar departamento'}),
        }
