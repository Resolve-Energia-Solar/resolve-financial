import logging
import os
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from financial.models import FinancialRecord
from financial.views import OmieIntegrationView
from resolve_crm.models import Sale
from decimal import Decimal
from django.core.exceptions import ValidationError
import requests


logger = logging.getLogger(__name__)


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
    if not instance.branch or not instance.branch.transfer_percentage and not instance.transfer_percentage:
        raise ValidationError("Percentual de Repasse não configurado para a filial ou para a venda.")
    
    if not created and instance.old_total_value is not None:
        if instance.old_total_value != instance.total_value or instance.old_transfer_percentage != instance.transfer_percentage:
            # Recalcula o valor total esperado para cada parcela
            transfer_percentage = instance.transfer_percentage if instance.transfer_percentage else instance.branch.transfer_percentage
            franchise_installments = instance.franchise_installments.all()
            
            if franchise_installments.exists():
                reference_value = sum(
                    product.reference_value if product.reference_value is not None else product.value
                    for product in instance.sale_products.all()
                )
                
                difference_value = instance.total_value - reference_value
                margin_7 = max(difference_value * Decimal("0.07"), Decimal("0.00"))
                transfer_percentage = transfer_percentage / 100
                
                total_value = round(
                    (reference_value * transfer_percentage) - margin_7 + difference_value,
                    3
                )

                # Ajustar parcelas proporcionalmente
                num_installments = franchise_installments.count()
                installment_value = round(total_value / num_installments, 6)

                for installment in franchise_installments:
                    installment.installment_value = installment_value
                    installment.full_clean()
                    installment.save()


@receiver(post_save, sender=FinancialRecord)
def request_responsible_approval(sender, instance, created, **kwargs):
    """
    Solicita a aprovação do responsável pelo usuário que criou o registro.
    """
    if created:
        if instance.category_code in ['2.02.94', '2.02.92']:
            instance.status = 'E'
            instance.save()
            logger.info(f"Registro Financeiro {instance.protocol} aprovado automaticamente.")
            try:
                OmieIntegrationView().create_payment_request(instance)
            except Exception as e:
                logger.error(f"Erro ao criar solicitação de pagamento no Omie: {e}")
                raise ValidationError(f"Erro ao criar solicitação de pagamento no Omie: {e}")
        else:
            FINANCIAL_RECORD_APPROVAL_URL = os.environ.get('FINANCIAL_RECORD_APPROVAL_URL', None)
            if not FINANCIAL_RECORD_APPROVAL_URL:
                raise Exception("URL de aprovação não configurada.")
            
            if instance.responsible:
                try:
                    # Enviar notificação para o responsável
                    url = FINANCIAL_RECORD_APPROVAL_URL
                    body = {
                        'id': instance.id,
                        'manager_email': instance.responsible.email,
                        'description': (
                            f'Solicitação de Pagamento nº {instance.protocol}\n'
                            f'Criada em: {instance.created_at.strftime("%d/%m/%Y %H:%M:%S")}\n'
                            f'Requisitante: {instance.requester.complete_name}\n'
                            f'Setor: {instance.requesting_department.name}\n'
                            f'Valor: R$ {instance.value:.2f}\n'
                            f'Descrição: {instance.notes}'
                        ),
                    }
                    response = requests.post(url, json=body)
                    response.raise_for_status()
                except requests.RequestException as e:
                    logger.error(f"Erro ao solicitar aprovação: {e}")
                    raise ValidationError(f"Erro ao solicitar aprovação: {e}")
            else:
                raise ValidationError("Responsável não configurado para a solicitação de pagamento.")
