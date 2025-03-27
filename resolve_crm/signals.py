from asyncio import Task
import sys
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
import requests

from resolve_crm.task import check_projects_and_update_sale_tag, update_or_create_sale_tag
from .models import Project, Sale
from core.models import Attachment,Webhook
import logging


logger = logging.getLogger(__name__)

# def send_webhook_request(web_hook_url, data, secret):
#     headers = {
#         'Content-Type': 'application/json',
#         'X-Hook-Secret': secret
#     }
#     try:
#         response = requests.post(web_hook_url, json=data, headers=headers)
#         response.raise_for_status()
#         logger.info(f"Webhook enviado com sucesso: {response.status_code}")
#     except requests.exceptions.RequestException as e:
#         logger.error(f"Erro ao enviar o webhook: {e}")


# def get_model_data(instance):
#     data = {}
#     for field in instance._meta.get_fields():
#         field_name = field.name
#         field_value = getattr(instance, field_name, None)

#         # Tratamento especial para relacionamentos
#         if field.one_to_many or field.many_to_many:
#             # Exemplo: retornar lista de IDs relacionados
#             field_value = [obj.id for obj in field_value.all()] if field_value else []
#         elif field.is_relation:
#             # Exemplo: retornar apenas ID do objeto relacionado
#             field_value = field_value.id if field_value else None
#         elif hasattr(field_value, 'isoformat'):
#             # Exemplo: datas e horários
#             field_value = field_value.isoformat()

#         data[field_name] = field_value
    
#     return data


# @receiver(post_save)
# def send_webhook_on_save(sender, instance, created, **kwargs):
#     # Ignora o sinal durante as migrações
#     if 'migrate' in sys.argv or 'test' in sys.argv:
#         return

#     try:
#         content_type = ContentType.objects.get_for_model(sender)
#     except ContentType.DoesNotExist:
#         # Retorna caso o ContentType ainda não exista
#         return

#     event_type = 'C' if created else 'U'
#     webhooks = Webhook.objects.filter(
#         content_type=content_type,
#         event=event_type,
#         is_active=True
#     )

#     if webhooks.exists():
#         data = get_model_data(instance)
        
#         for webhook in webhooks:
#             send_webhook_request(webhook.url, data, webhook.secret)


# @receiver(post_delete)
# def send_webhook_on_delete(sender, instance, **kwargs):
#     content_type = ContentType.objects.get_for_model(sender)

#     webhooks = Webhook.objects.filter(
#         content_type=content_type,
#         event='D',
#         is_active=True
#     )

#     if webhooks.exists():
#         data = get_model_data(instance)
        
#         for webhook in webhooks:
#             send_webhook_request(webhook.url, data, webhook.secret)


@receiver(post_save, sender=Attachment)
def attachment_changed(sender, instance, **kwargs):
    if instance.document_type and any(
        key in instance.document_type.name for key in ['CPF', 'RG', 'Contrato', 'CNH', 'homologador']
    ):
        if hasattr(instance.content_object, 'projects'):
            sale = instance.content_object
            # logger.info(f"📌 Signal: Anexo salvo - Sale ID: {sale.id}")
            # logger.info(f"📌 Signal: sale status - Sale ID: {sale.status}")
            check_projects_and_update_sale_tag.delay(sale.id, sale.status)


@receiver(post_save, sender=Sale)
def sale_changed(sender, instance, **kwargs):
    # logger.info(f"📌 Signal: Venda salva - Sale ID: {instance.id}")
    # logger.info(f"📌 Signal: sale status - Sale ID: {instance.status}")
    check_projects_and_update_sale_tag.delay(instance.id, instance.status)


@receiver(post_save, sender=Project)
def project_changed(sender, instance, **kwargs):
    sale = instance.sale
    # logger.info(f"📌 Signal: Projeto salvo - Sale ID: {sale.id}")
    # logger.info(f"📌 Signal: sale status - Sale ID: {sale.status}")
    if instance.is_released_to_engineering():
        update_or_create_sale_tag.delay(sale.id, sale.status)
