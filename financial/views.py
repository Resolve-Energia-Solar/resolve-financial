from api.views import BaseModelViewSet
from .models import *
from .serializers import *
from datetime import datetime
from django.utils import timezone


class FinancierViewSet(BaseModelViewSet):
    queryset = Financier.objects.all()
    serializer_class = FinancierSerializer


class PaymentViewSet(BaseModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def perform_create(self, serializer):
        # Remover os campos que não pertencem ao modelo antes de salvar
        create_installments = self.request.data.pop('create_installments', False)
        
        # Converter 'installments_number' para um inteiro
        num_installments = int(self.request.data.pop('installments_number', 0) or 0)

        # Salvar o objeto Payment
        instance = serializer.save()

        # Criar parcelas se solicitado
        if create_installments and num_installments > 0:
            self.create_installments(instance, num_installments)

    def create_installments(self, payment, num_installments):
        # Garantir que due_date seja um objeto datetime
        if isinstance(payment.due_date, str):
            payment.due_date = datetime.strptime(payment.due_date, '%Y-%m-%d')

        installment_amount = payment.value / num_installments

        for i in range(num_installments):
            PaymentInstallment.objects.create(
                payment=payment,
                installment_value=installment_amount,
                due_date=payment.due_date + timezone.timedelta(days=30 * i),
                installment_number=i + 1
            )


class PaymentInstallmentViewSet(BaseModelViewSet):
    queryset = PaymentInstallment.objects.all()
    serializer_class = PaymentInstallmentSerializer


class FranchiseInstallmentViewSet(BaseModelViewSet):
    queryset = FranchiseInstallment.objects.all()
    serializer_class = FranchiseInstallmentSerializer

    # def perform_create(self, serializer):
    #     sale = serializer.validated_data['sale']
    #     # repass_percentage = serializer.validated_data['repass_percentage']
    #     remaining_percentage = FranchiseInstallment.remaining_percentage(sale)

    #     if repass_percentage > remaining_percentage:
    #         raise ValidationError(
    #             {"repass_percentage": f"Percentual restante para esta venda é {remaining_percentage}%. "
    #                                   f"Não é possível adicionar {repass_percentage}%."}
    #         )
    #     serializer.save()


class FinancialRecordViewSet(BaseModelViewSet):
    queryset = FinancialRecord.objects.all()
    serializer_class = FinancialRecordSerializer
