from asyncio import Task
import sys
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
import requests
from .models import Lead, Sale, Task
from core.models import Webhook
import logging


logger = logging.getLogger(__name__)

def send_webhook_request(web_hook_url, data, secret):
    headers = {
        'Content-Type': 'application/json',
        'X-Hook-Secret': secret
    }
    try:
        response = requests.post(web_hook_url, json=data, headers=headers)
        response.raise_for_status()
        logger.info(f"Webhook enviado com sucesso: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao enviar o webhook: {e}")


def get_model_data(instance):
    if isinstance(instance, Lead):
        return {
            "id": instance.id,
            "name": instance.name,
            "type": instance.get_type_display(), 
            "byname": instance.byname,
            "first_document": instance.first_document,
            "second_document": instance.second_document,
            "birth_date": instance.birth_date.isoformat() if instance.birth_date else None,
            "gender": instance.get_gender_display(),
            "contact_email": instance.contact_email,
            "phone": instance.phone,
            "addresses": [address.id for address in instance.addresses.all()],
            "customer": instance.customer.id if instance.customer else None,
            "origin": instance.origin,
            "seller": instance.seller.id if instance.seller else None,
            "sdr": instance.sdr.id if instance.sdr else None,
            "funnel": instance.get_funnel_display(), 
            "column": instance.column.id if instance.column else None,
            "is_deleted": instance.is_deleted,
            "created_at": instance.created_at.isoformat(),
        }
    
    elif isinstance(instance, Task):
        return {
            "id": instance.id,
            "lead": instance.lead.id,
            "title": instance.title,
            "delivery_date": instance.delivery_date.isoformat(),
            "description": instance.description,
            "status": instance.get_status_display(),
            "task_type": instance.get_task_type_display(),
            "members": [member.id for member in instance.members.all()],
            "is_deleted": instance.is_deleted,
            "created_at": instance.created_at.isoformat(),
        }
        
    elif isinstance(instance, Sale):
        return {
            "id": instance.id,
            "customer": instance.customer.id,
            "seller": instance.seller.id,
            "sales_supervisor": instance.sales_supervisor.id,
            "sales_manager": instance.sales_manager.id,
            "total_value": instance.total_value,
            "contract_number": instance.contract_number,
            "signature_date": instance.signature_date.isoformat() if instance.signature_date else None,
            "branch": instance.branch.id,
            "marketing_campaign": instance.marketing_campaign.id if instance.marketing_campaign else None,
            "is_pre_sale": instance.is_pre_sale,
            "status": instance.get_status_display(),
            "transfer_percentage": str(instance.transfer_percentage) if instance.transfer_percentage else None,
            "products": [product.id for product in instance.products.all()],
            "financial_completion_date": instance.financial_completion_date.isoformat() if instance.financial_completion_date else None,
            "created_at": instance.created_at.isoformat(),
        }

    return {
        "id": instance.id,
    }


@receiver(post_save)
def send_webhook_on_save(sender, instance, created, **kwargs):
    # Ignora o sinal durante as migrações
    if 'migrate' in sys.argv or 'test' in sys.argv:
        return

    try:
        content_type = ContentType.objects.get_for_model(sender)
    except ContentType.DoesNotExist:
        # Retorna caso o ContentType ainda não exista
        return

    event_type = 'C' if created else 'U'
    webhooks = Webhook.objects.filter(
        content_type=content_type,
        event=event_type,
        is_active=True
    )

    if webhooks.exists():
        data = get_model_data(instance)
        
        for webhook in webhooks:
            send_webhook_request(webhook.url, data, webhook.secret)


@receiver(post_delete)
def send_webhook_on_delete(sender, instance, **kwargs):
    content_type = ContentType.objects.get_for_model(sender)

    webhooks = Webhook.objects.filter(
        content_type=content_type,
        event='D',
        is_active=True
    )

    if webhooks.exists():
        data = get_model_data(instance)
        
        for webhook in webhooks:
            send_webhook_request(webhook.url, data, webhook.secret)
