from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from resolve_crm.models import Sale
from decimal import Decimal
from django.core.exceptions import ValidationError

@receiver(pre_save, sender=Sale)
def store_old_total_value(sender, instance, **kwargs):
    """
    Antes de salvar, armazena o valor antigo de total_value na instância.
    """
    if instance.pk:
        old_instance = Sale.objects.get(pk=instance.pk)
        instance.old_total_value = old_instance.total_value
        old_transfer_percentage = instance.transfer_percentage
        instance.old_transfer_percentage = old_transfer_percentage
    else:
        instance.old_total_value = None 


@receiver(post_save, sender=Sale)
def adjust_franchise_installments_on_sale_update(sender, instance, created, **kwargs):
    """
    Ajusta as parcelas do franquiado se o valor total da venda foi alterado.
    """
    
    if not instance.branch or not instance.branch.transfer_percentage or not instance.transfer_percentage:
        raise ValidationError("Percentual de Repasse não configurado para a filial ou para a venda.")
        
    
    if not created and instance.old_total_value is not None:
        if instance.old_total_value != instance.total_value or instance.old_transfer_percentage != instance.transfer_percentage:
            # Recalcula o valor total esperado para cada parcela
            transfer_percentage = instance.transfer_percentage if instance.transfer_percentage else instance.branch.transfer_percentage
            franchise_installments = instance.franchise_installments.all()
            if franchise_installments.exists():
                reference_value = sum(
                    instance.sale_products.all().values_list("reference_value", flat=True)
                )
                difference_value = instance.total_value - reference_value
                margin_7 = max(difference_value * Decimal("0.07"), Decimal("0.00"))
                transfer_percentage =  transfer_percentage / 100
                total_value = round(
                    (reference_value * (transfer_percentage)) - margin_7 + difference_value,
                    3
                )

                # Ajustar parcelas proporcionalmente
                num_installments = franchise_installments.count()
                installment_value = round(total_value / num_installments, 6)

                for installment in franchise_installments:
                    installment.installment_value = installment_value
                    installment.full_clean()  # Validar antes de salvar
                    installment.save()
