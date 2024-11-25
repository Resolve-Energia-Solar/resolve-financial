from django.db.models.signals import post_save
from django.dispatch import receiver
from resolve_crm.models import Sale
from .models import FranchiseInstallment
from decimal import Decimal


@receiver(post_save, sender=Sale)
def create_initial_installment(sender, instance, created, **kwargs):
    if created:  # Apenas para vendas recém-criadas

        reference_value = sum(instance.sale_products.all().values_list("reference_value", flat=True))
        difference_value = instance.total_value - reference_value
        
        if difference_value <= 0:
            margin_7 = 0
        else:
            margin_7 = difference_value * Decimal("0.07")
        
        if difference_value <= 0:
            installment_value = reference_value * (1 - instance.transfer_percentage / 100) - difference_value
        else:
            installment_value = reference_value * (1 - instance.transfer_percentage / 100) + difference_value - margin_7 
            
        FranchiseInstallment.objects.create(
            sale=instance,
            installment_value=installment_value,
            # due_date=instance.created_at + timedelta(days=30),  # Exemplo: 30 dias após a criação da venda
        )