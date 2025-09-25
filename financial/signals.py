import logging
import os
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from financial.models import FinancialRecord
from financial.views import OmieIntegrationView
from resolve_crm.models import Sale
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
import requests
from .task import notify_requester_on_audit_change_task


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
    print("Ajustando parcelas de franquia após atualização da venda...")
    if created:
        return

    if not instance.branch or not instance.branch.transfer_percentage and not instance.transfer_percentage:
        raise ValidationError("Percentual de Repasse não configurado para a filial ou para a venda.")

    if instance.old_total_value != instance.total_value or instance.old_transfer_percentage != instance.transfer_percentage:
        franchise_installments = instance.franchise_installments.all()
        if not franchise_installments.exists():
            return

        reference_value = sum(
            p.reference_value or Decimal("0.00")
            for p in instance.sale_products.all()
        )

        total_value = instance.calculate_franchise_installment_value(reference_value)
        num_installments = franchise_installments.count()
        installment_value = round(total_value / num_installments, 6)

        for installment in franchise_installments:
            installment.installment_value = installment_value
            installment.full_clean()
            installment.save()



@receiver(pre_save, sender=FinancialRecord)
def store_old_audit_status(sender, instance, **kwargs):
    """
    Antes de salvar, armazena o valor antigo de audit_status na instância.
    """
    if instance.pk:
        old_instance = FinancialRecord.objects.get(pk=instance.pk)
        instance.old_audit_status = old_instance.audit_status
    else:
        instance.old_audit_status = None


@receiver(post_save, sender=FinancialRecord)
def send_to_omie_on_audit_approval(sender, instance, created, **kwargs):
    """
    Envia para OMIE quando audit_status for alterado para 'A' (Aprovado).
    """
    if not created and hasattr(instance, 'old_audit_status'):
        # Verifica se o audit_status foi alterado para 'A'
        if instance.old_audit_status != 'A' and instance.audit_status == 'A':
            logger.info(f"Audit status changed to 'A' for financial record {instance.protocol}. Sending to OMIE...")
            try:
                # Utiliza a task para envio assíncrono ao OMIE
                from .task import send_to_omie_task
                send_to_omie_task.delay(instance.id)
                logger.info(f"Financial record {instance.protocol} sent to OMIE processing queue")
            except Exception as e:
                logger.error(f"Erro ao enviar registro financeiro {instance.protocol} para OMIE: {e}")


@receiver(post_save, sender=FinancialRecord)
def track_audit_status_changes(sender, instance, created, **kwargs):
    """
    Atualiza os campos audit_by e audit_response_date quando audit_status for alterado.
    """
    if not created and hasattr(instance, 'old_audit_status'):
        # Verifica se o audit_status foi alterado
        if instance.old_audit_status != instance.audit_status:
            # Obtém o usuário atual através do simple_history
            current_user = None
            
            # Tenta obter o usuário através do middleware do simple_history
            try:
                import threading
                # O HistoryRequestMiddleware armazena o usuário em um local thread-local
                local = threading.local()
                if hasattr(local, 'user'):
                    current_user = local.user
                else:
                    # Fallback: verifica se existe no contexto do Django
                    from django import get_version
                    # Para Django com simple_history, o usuário pode estar em _request_middleware_context
                    context = getattr(threading.current_thread(), '_request_middleware_context', None)
                    if context and hasattr(context, 'user'):
                        current_user = context.user
            except:
                pass
            
            # Se não conseguir obter o usuário, log de warning (mas continua a execução)
            if not current_user or (hasattr(current_user, 'is_authenticated') and not current_user.is_authenticated):
                logger.warning(f"Não foi possível identificar o usuário que alterou o audit_status do registro {instance.protocol}")
                current_user = None
            
            # Prepara os campos para atualização (apenas se não foram definidos pelo serializer)
            update_fields = {}
            
            # Só atualiza audit_response_date se ainda não foi definido
            if not instance.audit_response_date:
                update_fields['audit_response_date'] = timezone.now()
            
            # Só atualiza audit_by se conseguiu identificar um usuário válido e ainda não foi definido
            if (not instance.audit_by and 
                current_user and 
                hasattr(current_user, 'is_authenticated') and 
                current_user.is_authenticated):
                update_fields['audit_by'] = current_user
            
            # Salva apenas se há campos para atualizar
            if update_fields:
                FinancialRecord.objects.filter(pk=instance.pk).update(**update_fields)
            
            logger.info(f"Audit tracking updated for financial record {instance.protocol}: status changed from '{instance.old_audit_status}' to '{instance.audit_status}', user: {current_user.email if current_user else 'Unknown'}")

            # Envia notificação ao solicitante quando o audit_status for Cancelado ou Reprovado
            try:
                if instance.audit_status in ("C", "R"):
                    notify_requester_on_audit_change_task.delay(instance.id)
            except Exception as e:
                logger.error(
                    f"Erro ao enfileirar notificação ao solicitante para o registro {instance.protocol}: {e}"
                )


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
                    
                    integration_code = response.headers.get('x-ms-workflow-run-id')
                    if integration_code:
                        instance.responsible_request_integration_code = integration_code
                        instance.save()
                except requests.RequestException as e:
                    logger.error(f"Erro ao solicitar aprovação: {e}")
                    raise ValidationError(f"Erro ao solicitar aprovação: {e}")
            else:
                raise ValidationError("Responsável não configurado para a solicitação de pagamento.")
