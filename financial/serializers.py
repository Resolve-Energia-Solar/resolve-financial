from django.forms import ValidationError
from dotenv import load_dotenv
from accounts.serializers import BaseSerializer
from financial.models import FinancialRecord, FranchiseInstallment, Payment, PaymentInstallment, Financier
from rest_framework.serializers import SerializerMethodField
from django.db import transaction


load_dotenv()


class FinancierSerializer(BaseSerializer):
    class Meta:
        model = Financier
        fields = '__all__'

class PaymentInstallmentSerializer(BaseSerializer):
    class Meta:
        model = PaymentInstallment
        fields = '__all__'

class PaymentSerializer(BaseSerializer):
    is_paid = SerializerMethodField()
    total_paid = SerializerMethodField()
    percentual_paid = SerializerMethodField()

    class Meta:
        model = Payment
        fields = '__all__'
        
    def validate(self, data):
        if data.get('payment_type') == 'F' and not data.get('financier'):
            raise ValidationError("Financiadora é obrigatória para pagamentos Financiados.")
        return data

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
    difference_value = SerializerMethodField()
    total_value = SerializerMethodField()
    transfer_percentage = SerializerMethodField()
    percentage = SerializerMethodField()
    margin_7 = SerializerMethodField()
    is_payment_released = SerializerMethodField()
    reference_value = SerializerMethodField()
    payments_methods = SerializerMethodField()

    class Meta:
        model = FranchiseInstallment
        fields = '__all__'
    
    def get_payments_methods(self, obj):
        return obj.payments_methods()
    
    def get_reference_value(self, obj):
        return float(obj.reference_value()) if obj.reference_value() is not None else 0.0
        
    def get_is_payment_released(self, obj):
        return obj.is_payment_released
        
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
    class Meta:
        model = FinancialRecord
        fields = '__all__'
