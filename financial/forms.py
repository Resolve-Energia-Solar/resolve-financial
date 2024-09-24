from django import forms
from .models import PaymentRequest
from django_select2.forms import Select2Widget, HeavySelect2Widget


class PaymentRequestForm(forms.ModelForm):
    
    class Meta:
        model = PaymentRequest
        fields = '__all__'
        exclude = ['created_at', 'id_omie', 'supplier_name', 'category_name', 'protocol', 'requester', 'manager', 'department', 'requesting_status', 'manager_status', 'manager_status_completion_date', 'financial_status', 'financial_status_completion_date']
        labels = {
            'supplier': 'Beneficiário (CPF/CNPJ)'
        }
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'mask-money', 'type': 'text'}),
            'requester': Select2Widget(),
            'manager': Select2Widget(),
            'department': Select2Widget(),
            'supplier': HeavySelect2Widget(data_view='financial:suppliers_list', attrs={'data-placeholder': 'Selecionar fornecedor', 'data-minimum-input-length': 11}),
            'category': HeavySelect2Widget(data_view='financial:categories_list', attrs={'data-placeholder': 'Selecionar categoria', 'data-minimum-input-length': 3}),
            'id_sale': Select2Widget(attrs={'data-placeholder': 'Selecionar venda', 'data-minimum-input-length': 3}),
            'service_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_method': Select2Widget(),
            'causative_department': Select2Widget(),
            'id_bank_account': Select2Widget(),
        }
