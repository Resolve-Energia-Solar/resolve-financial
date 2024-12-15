import os
import requests
from dotenv import load_dotenv
from accounts.models import Address, User
from accounts.serializers import AddressSerializer, BaseSerializer, RelatedUserSerializer
from resolve_crm.serializers import SaleSerializer
from financial.models import FinancialRecord, FranchiseInstallment, Payment, PaymentInstallment, Financier
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import SerializerMethodField
from resolve_crm.models import Sale
from django.db import transaction


load_dotenv()


class FinancierSerializer(BaseSerializer):

    # Para leitura: usar serializador completo
    address = AddressSerializer(read_only=True)

    # Para escrita: usar apenas ID
    address_id = PrimaryKeyRelatedField(queryset=Address.objects.all(), write_only=True, source='address')


    class Meta:
        model = Financier
        fields = '__all__'


class PaymentInstallmentSerializer(BaseSerializer):
    payment = PrimaryKeyRelatedField(queryset=Payment.objects.all(), required=False, write_only=True)

    class Meta:
        model = PaymentInstallment
        fields = '__all__'

class PaymentSerializer(BaseSerializer):
    sale = SaleSerializer(read_only=True)
    financier = FinancierSerializer(read_only=True)
    installments = PaymentInstallmentSerializer(many=True, required=False)
    borrower = RelatedUserSerializer(read_only=True)
    sale_id = PrimaryKeyRelatedField(queryset=Sale.objects.all(), write_only=True, source='sale')
    financier_id = PrimaryKeyRelatedField(queryset=Financier.objects.all(), write_only=True, source='financier')

    is_paid = SerializerMethodField()
    total_paid = SerializerMethodField()
    percentual_paid = SerializerMethodField()
    borrower_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='borrower')

    class Meta:
        model = Payment
        fields = '__all__'

    def get_is_paid(self, obj):
        return obj.is_paid

    def get_total_paid(self, obj):
        return obj.total_paid

    def get_percentual_paid(self, obj):
        return obj.percentual_paid

    @transaction.atomic
    def create(self, validated_data):
        # Extrair e remover os dados das parcelas antes de salvar o pagamento
        installments_data = validated_data.pop('installments', None)

        # Criar a instância de Payment usando os dados validados
        instance = super().create(validated_data)

        # Se houver dados de parcelas, criar as parcelas associadas
        if installments_data:
            for installment_data in installments_data:
                installment_data.pop('payment', None)
                PaymentInstallment.objects.create(payment=instance, **installment_data)

        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        installments_data = validated_data.pop('installments', None)

        # Atualizar a instância de Payment
        instance = super().update(instance, validated_data)

        if installments_data is not None:
            existing_installment_ids = [inst.id for inst in instance.installments.all()]
            new_installment_ids = [inst.get('id') for inst in installments_data if inst.get('id')]

            # Deletar parcelas que não estão mais presentes nos novos dados
            for installment_id in existing_installment_ids:
                if installment_id not in new_installment_ids:
                    PaymentInstallment.objects.filter(id=installment_id).delete()

            for installment_data in installments_data:
                installment_id = installment_data.get('id', None)
                
                installment_data.pop('payment', None)

                if installment_id:
                    PaymentInstallment.objects.update_or_create(
                        id=installment_id,
                        payment=instance,
                        defaults=installment_data
                    )
                else:
                    PaymentInstallment.objects.create(payment=instance, **installment_data)

        return instance


class FranchiseInstallmentSerializer(BaseSerializer):
    # Campos para leitura
    sale = SaleSerializer(read_only=True)
    difference_value = SerializerMethodField()
    total_value = SerializerMethodField()
    transfer_percentage = SerializerMethodField()
    percentage = SerializerMethodField()
    margin_7 = SerializerMethodField()
    
    # Campos para escrita
    sale_id = PrimaryKeyRelatedField(queryset=Sale.objects.all(), write_only=True, source='sale')

    class Meta:
        model = FranchiseInstallment
        fields = [
            'id', 'sale', 'status', 'installment_value', 'is_paid', 'paid_at', 'created_at',
            'difference_value', 'total_value', 'transfer_percentage', 'percentage', 'margin_7',
            'sale_id'
        ]
        
    def get_difference_value(self, obj):
        return float(obj.difference_value) if obj.difference_value is not None else 0.0

    def get_total_value(self, obj):
        return float(obj.total_value) if obj.total_value is not None else 0.0

    def get_transfer_percentage(self, obj):
        return f"{obj.transfer_percentage}" if obj.transfer_percentage else "0%"

    def get_percentage(self, obj):
        return f"{obj.percentage}" if obj.percentage else "0%"
    
    def get_margin_7(self, obj):
        return obj.margin_7


class FinancialRecordSerializer(BaseSerializer):
    # Campos para leitura
    requester = RelatedUserSerializer(read_only=True)
    responsible = RelatedUserSerializer(read_only=True)
    client_supplier_name = SerializerMethodField()

    # Campos para escrita
    requester_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='requester')
    responsible_id = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='responsible')

    class Meta:
        model = FinancialRecord
        fields = '__all__'

    def get_client_supplier_name(self, obj):
        headers = {
            'Content-Type': 'application/json'
        }
        body = {
            "call": "ConsultarCliente",
            "app_key": os.environ.get('OMIE_ACESSKEY'),
            "app_secret": os.environ.get('OMIE_ACESSTOKEN'),
            "param": [
                {
                    "codigo_cliente_omie": obj.client_supplier_code,
                    "codigo_cliente_integracao": ""
                }
            ]
        }
        print(f"Request Headers: {headers}")
        print(f"Request Body: {body}")
        response = requests.post(f"{os.environ.get('OMIE_API_URL')}/geral/clientes/", headers=headers, json=body)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
        return response.json().get('nome_fantasia') if response.status_code == 200 else None
