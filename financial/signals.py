from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from resolve_crm.models import Sale
from decimal import Decimal

@receiver(pre_save, sender=Sale)
def store_old_total_value(sender, instance, **kwargs):
    """
    Antes de salvar, armazena o valor antigo de total_value na instância.
    """
    print(f"Pré-Save: {instance.pk}")
    if instance.pk:  # Verifica se a instância já existe no banco (update)
        old_instance = Sale.objects.get(pk=instance.pk)
        instance.old_total_value = old_instance.total_value
    else:
        instance.old_total_value = None  # Para novas instâncias
        
    print(f"Valor antigo: {instance.old_total_value}")


@receiver(post_save, sender=Sale)
def adjust_franchise_installments_on_sale_update(sender, instance, created, **kwargs):
    """
    Ajusta as parcelas do franquiado se o valor total da venda foi alterado.
    """
    if not created and instance.old_total_value is not None:  # Garantir que não é criação e que temos um valor antigo
        if instance.old_total_value != instance.total_value:
            print(f"Valor antigo: {instance.old_total_value}")
            print(f"Valor atualizado: {instance.total_value}")

            # Recalcula o valor total esperado para cada parcela
            franchise_installments = instance.franchise_installments.all()
            if franchise_installments.exists():
                reference_value = sum(
                    instance.sale_products.all().values_list("reference_value", flat=True)
                )
                difference_value = instance.total_value - reference_value
                margin_7 = max(difference_value * Decimal("0.07"), Decimal("0.00"))
                transfer_percentage = instance.transfer_percentage / 100
                total_value = round(
                    (reference_value * (1 - transfer_percentage)) - margin_7 + difference_value,
                    3
                )

                print(f"Novo Total Value Calculado: {total_value}")

                # Ajustar parcelas proporcionalmente
                num_installments = franchise_installments.count()
                installment_value = round(total_value / num_installments, 6)

                for installment in franchise_installments:
                    installment.installment_value = installment_value
                    installment.full_clean()  # Validar antes de salvar
                    installment.save()

                print("Parcelas recalculadas com sucesso.")
