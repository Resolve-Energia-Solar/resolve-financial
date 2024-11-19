from accounts.models import Address
from api.serializers.accounts import AddressSerializer, BaseSerializer, RelatedUserSerializer
from api.serializers.resolve_crm import SaleSerializer
from financial.models import Payment, PaymentInstallment, Financier
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import SerializerMethodField

from resolve_crm.models import Sale
from django.db import transaction


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



from datetime import datetime
from rest_framework import serializers

class PaymentSerializer(BaseSerializer):
    sale = SaleSerializer(read_only=True)
    financier = FinancierSerializer(read_only=True)
    installments = PaymentInstallmentSerializer(many=True, required=False)
    borrower = RelatedUserSerializer(read_only=True)
    sale_id = serializers.PrimaryKeyRelatedField(queryset=Sale.objects.all(), write_only=True, source='sale')
    financier_id = serializers.PrimaryKeyRelatedField(queryset=Financier.objects.all(), write_only=True, source='financier')

    is_paid = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    percentual_paid = serializers.SerializerMethodField()
    borrower_id = serializers.PrimaryKeyRelatedField(queryset=Sale.objects.all(), write_only=True, source='borrower')

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
