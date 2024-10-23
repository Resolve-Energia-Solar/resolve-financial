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


class PaymentSerializer(BaseSerializer):

    # Para leitura: usar serializador completo
    sale = SaleSerializer(read_only=True)
    financier = FinancierSerializer(read_only=True)

    # Para escrita: usar apenas ID
    sale_id = PrimaryKeyRelatedField(queryset=Sale.objects.all(), write_only=True, source='sale')
    financier_id = PrimaryKeyRelatedField(queryset=Financier.objects.all(), write_only=True, source='financier')

    class Meta:
        model = Payment
        fields = '__all__'


class PaymentInstallmentSerializer(BaseSerializer):
    class Meta:
        model = PaymentInstallment
        fields = '__all__'
