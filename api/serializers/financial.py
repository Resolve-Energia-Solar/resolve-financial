from accounts.models import Address
from api.serializers.accounts import AddressSerializer, BaseSerializer
from api.serializers.resolve_crm import SaleSerializer
from financial.models import Payment, PaymentInstallment, Financier
from rest_framework.relations import PrimaryKeyRelatedField

from resolve_crm.models import Sale


class FinancierSerializer(BaseSerializer):

    # Para leitura: usar serializador completo
    address = AddressSerializer(read_only=True)

    # Para escrita: usar apenas ID
    address_id = PrimaryKeyRelatedField(queryset=Address.objects.all(), write_only=True, source='address')


    class Meta:
        model = Financier
        fields = '__all__'


class PaymentInstallmentSerializer(BaseSerializer):
    class Meta:
        model = PaymentInstallment
        fields = '__all__'


class PaymentSerializer(BaseSerializer):
    sale = SaleSerializer(read_only=True)
    financier = FinancierSerializer(read_only=True)
    installments = PaymentInstallmentSerializer(many=True, required=False)

    sale_id = PrimaryKeyRelatedField(queryset=Sale.objects.all(), write_only=True, source='sale')
    financier_id = PrimaryKeyRelatedField(queryset=Financier.objects.all(), write_only=True, source='financier')

    class Meta:
        model = Payment
        fields = '__all__'

    def update(self, instance, validated_data):
        raw_data = self.initial_data

        installments_data = raw_data.pop('installments', None)
        
        # Atualiza a instância de Payment
        instance = super().update(instance, raw_data)

        if installments_data is not None:
            existing_installment_ids = [inst.id for inst in instance.installments.all()]
            new_installment_ids = [inst.get('id') for inst in installments_data if inst.get('id')]

            # Delete installments that are not in the new installments data
            for installment_id in existing_installment_ids:
                if installment_id not in new_installment_ids:
                    PaymentInstallment.objects.filter(id=installment_id).delete()

            for installment_data in installments_data:
                installment_id = installment_data.get('id', None)
                
                # Remover 'payment' do installment_data para evitar duplicidade
                installment_data.pop('payment', None)
                
                if installment_id:
                    # Atualiza a parcela existente ou cria uma nova, se não existir
                    PaymentInstallment.objects.update_or_create(
                        id=installment_id,
                        payment=instance,
                        defaults=installment_data
                    )
                else:
                    # Criar nova parcela se o ID não for fornecido
                    PaymentInstallment.objects.create(payment=instance, **installment_data)

        return instance
