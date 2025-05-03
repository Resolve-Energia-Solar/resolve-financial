from dotenv import load_dotenv

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.forms import ValidationError

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import SerializerMethodField
from rest_framework import serializers

from accounts.serializers import BaseSerializer

from .models import (
    BankDetails,
    FinancialRecord,
    FranchiseInstallment,
    Payment,
    PaymentInstallment,
    Financier,
)

load_dotenv()


class FinancierSerializer(BaseSerializer):
    class Meta:
        model = Financier
        fields = "__all__"


class PaymentInstallmentSerializer(BaseSerializer):
    class Meta:
        model = PaymentInstallment
        fields = "__all__"


class PaymentSerializer(BaseSerializer):
    is_paid = SerializerMethodField()
    total_paid = SerializerMethodField()
    percentual_paid = SerializerMethodField()

    class Meta:
        model = Payment
        fields = "__all__"

    def validate(self, data):
        if data.get("payment_type") == "F" and not data.get("financier"):
            raise ValidationError(
                "Financiadora é obrigatória para pagamentos Financiados."
            )
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
        installments_data = validated_data.pop("installments", None)

        # Criar a instância de Payment usando os dados validados
        instance = super().create(validated_data)

        # Se houver dados de parcelas, criar as parcelas associadas
        if installments_data:
            for installment_data in installments_data:
                installment_data.pop("payment", None)
                PaymentInstallment.objects.create(payment=instance, **installment_data)

        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        installments_data = validated_data.pop("installments", None)

        # Atualizar a instância de Payment
        instance = super().update(instance, validated_data)

        if installments_data is not None:
            existing_installment_ids = [inst.id for inst in instance.installments.all()]
            new_installment_ids = [
                inst.get("id") for inst in installments_data if inst.get("id")
            ]

            # Deletar parcelas que não estão mais presentes nos novos dados
            for installment_id in existing_installment_ids:
                if installment_id not in new_installment_ids:
                    PaymentInstallment.objects.filter(id=installment_id).delete()

            for installment_data in installments_data:
                installment_id = installment_data.get("id", None)

                installment_data.pop("payment", None)

                if installment_id:
                    PaymentInstallment.objects.update_or_create(
                        id=installment_id, payment=instance, defaults=installment_data
                    )
                else:
                    PaymentInstallment.objects.create(
                        payment=instance, **installment_data
                    )

        return instance


class FranchiseInstallmentSerializer(BaseSerializer):
    difference_value = serializers.ReadOnlyField()
    total_value = serializers.ReadOnlyField()
    transfer_percentage = serializers.ReadOnlyField()
    percentage = serializers.ReadOnlyField()
    margin_7 = serializers.ReadOnlyField()
    is_payment_released = serializers.ReadOnlyField()
    reference_value = serializers.ReadOnlyField()
    marketing_tax_value = serializers.ReadOnlyField()
    remaining_percentage = serializers.ReadOnlyField()
    total_reference_value = serializers.ReadOnlyField()

    payments_methods = serializers.SerializerMethodField()

    class Meta:
        model = FranchiseInstallment
        fields = "__all__"
        
    def get_payments_methods(self, obj):
        return obj.payments_methods()

class FinancialRecordSerializer(BaseSerializer):
    class Meta:
        model = FinancialRecord
        fields = "__all__"


class BankDetailsSerializer(BaseSerializer):
    class Meta:
        model = BankDetails
        fields = "__all__"

    def validate(self, data):
        errors = {}
        at = data.get("account_type")
        pk = data.get("pix_key")
        pkt = data.get("pix_key_type")
        ag = data.get("agency_number")
        ac = data.get("account_number")
        fi = data.get("financial_instituition")

        if at == "X":
            if not pk:
                errors["pix_key"] = "Obrigatório para contas do tipo PIX."
            if not pkt:
                errors["pix_key_type"] = "Obrigatório para contas do tipo PIX."
            if ag:
                errors["agency_number"] = (
                    "Não deve ser preenchida para contas do tipo PIX."
                )
            if ac:
                errors["account_number"] = (
                    "Não deve ser preenchida para contas do tipo PIX."
                )

            if pkt == "CPF" and (not pk.isdigit() or len(pk) != 11):
                errors["pix_key"] = "Deve conter 11 dígitos numéricos."
            if pkt == "CNPJ" and (not pk.isdigit() or len(pk) != 14):
                errors["pix_key"] = "Deve conter 14 dígitos numéricos."
            if pkt == "EMAIL":
                try:
                    validate_email(pk)
                except DjangoValidationError:
                    errors["pix_key"] = "Deve ser um e-mail válido."
            if pkt == "PHONE" and (not pk.isdigit() or len(pk) != 11):
                errors["pix_key"] = "Deve conter 11 dígitos numéricos, ex: 11999999999."
            if pkt == "RANDOM" and len(pk or "") != 32:
                errors["pix_key"] = "Deve conter 32 caracteres."
        else:
            if not fi:
                errors["financial_instituition"] = (
                    "Obrigatório para contas Corrente ou Poupança."
                )
            if not ag:
                errors["agency_number"] = (
                    "Obrigatório para contas Corrente ou Poupança."
                )
            if not ac:
                errors["account_number"] = (
                    "Obrigatório para contas Corrente ou Poupança."
                )

        if errors:
            raise ValidationError(errors)

        return data
