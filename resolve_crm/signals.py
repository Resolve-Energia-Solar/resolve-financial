import json
import requests
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Lead, Webhook
from django.contrib.contenttypes.models import ContentType

def send_webhook_request(web_hook_url, data, secret):
    headers = {
        'Content-Type': 'application/json',
        'X-Hook-Secret': secret
    }
    try:
        response = requests.post(web_hook_url, data=json.dumps(data), headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar o webhook: {e}")

@receiver(post_save, sender=Lead)
def send_webhook_on_save(instance, created, **kwargs):
    event_type = 'C' if created else 'U'

    lead_content_type = ContentType.objects.get_for_model(Lead)

    webhooks = Webhook.objects.filter(
        content_type=lead_content_type,
        event=event_type,
        is_active=True
    )

    if webhooks.exists():
            data = {
      "id": instance.id,
      "name": instance.name,
      "type": instance.type,
      "byname": instance.byname,
      "first_document": instance.first_document,
      "second_document": instance.second_document,
      "birth_date": instance.birth_date.isoformat() if instance.birth_date else None,
      "gender": instance.gender,
      "contact_email": instance.contact_email,
      "phone": instance.phone,
      "addresses": [address.id for address in instance.addresses.all()],
      "customer": instance.customer.id if instance.customer else None,
      "origin": instance.origin,
      "seller": instance.seller.id if instance.seller else None,
      "sdr": instance.sdr.id if instance.sdr else None,
      "funnel": instance.funnel,
      "column": instance.column.id if instance.column else None,
      "is_deleted": instance.is_deleted,
      "created_at": instance.created_at.isoformat(),
    }
    for webhook in webhooks:
        send_webhook_request(webhook.url, data, webhook.secret)


@receiver(post_delete, sender=Lead)
def send_webhook_on_delete(instance, **kwargs):
    lead_content_type = ContentType.objects.get_for_model(Lead)

    webhooks = Webhook.objects.filter(
        content_type=lead_content_type,
        event='D',  # 'D' para Delete
        is_active=True
    )

    if webhooks.exists():
            data = {
            "id": instance.id,
            "name": instance.name,
            "type": instance.type,
            "byname": instance.byname,
            "first_document": instance.first_document,
            "second_document": instance.second_document,
            "birth_date": instance.birth_date.isoformat() if instance.birth_date else None,
            "gender": instance.gender,
            "contact_email": instance.contact_email,
            "phone": instance.phone,
            "addresses": [address.id for address in instance.addresses.all()],
            "customer": instance.customer.id if instance.customer else None,
            "origin": instance.origin,
            "seller": instance.seller.id if instance.seller else None,
            "sdr": instance.sdr.id if instance.sdr else None,
            "funnel": instance.funnel,
            "column": instance.column.id if instance.column else None,
            "is_deleted": instance.is_deleted,
            "created_at": instance.created_at.isoformat(),
          }
    for webhook in webhooks:
        send_webhook_request(webhook.url, data, webhook.secret)
        
        