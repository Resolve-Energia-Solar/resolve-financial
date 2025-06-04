from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from core.models import Process, StepName, Webhook
import requests
import sys
import logging
from core.task import send_webhook_request_async

logger = logging.getLogger(__name__)

SUPPORTED_MODELS = ['Sale', 'Schedule', 'Project']

# @receiver(post_save, sender=Process)
# def update_current_steps(sender, instance, created, **kwargs):
#     etapas = instance.steps or []
#     concluidas = {et.get("id") for et in etapas if et.get("is_completed")}
#     liberadas = []

#     for etapa in etapas:
#         if etapa.get("is_completed"):
#             continue
#         dependencias = etapa.get("dependencies", [])
#         if all(dep in concluidas for dep in dependencias):
#             liberadas.append(etapa)

#     step_ids = []
#     for etapa in liberadas:
#         step_value = etapa.get("step")
#         if isinstance(step_value, dict):
#             step_ids.append(step_value.get("id"))
#         elif isinstance(step_value, list) and len(step_value) == 2:
#             _, step_id = step_value
#             step_ids.append(step_id)
#     steps = StepName.objects.filter(id__in=step_ids)
#     instance.current_step.set(steps)
    

@receiver(post_save)
def send_webhook_on_save(sender, instance, created, **kwargs):
    if 'migrate' in sys.argv or 'test' in sys.argv:
        return

    if sender.__name__ not in SUPPORTED_MODELS:
        return

    try:
        content_type = ContentType.objects.get_for_model(sender)
    except ContentType.DoesNotExist:
        return

    event_type = 'C' if created else 'U'
    webhooks = Webhook.objects.filter(
        content_type=content_type,
        event=event_type,
        is_active=True
    )

    if not webhooks.exists():
        return

    model_label = instance._meta.label
    instance_id = instance.pk

    for webhook in webhooks:
        send_webhook_request_async.delay(
            webhook.url,
            model_label,
            instance_id,
            webhook.secret,
            webhook.id
        )


@receiver(post_delete)
def send_webhook_on_delete(sender, instance, **kwargs):
    if 'migrate' in sys.argv or 'test' in sys.argv:
        return

    if sender.__name__ not in SUPPORTED_MODELS:
        return

    try:
        content_type = ContentType.objects.get_for_model(sender)
    except ContentType.DoesNotExist:
        return

    webhooks = Webhook.objects.filter(
        content_type=content_type,
        event='D',
        is_active=True
    )

    if not webhooks.exists():
        return

    model_label = instance._meta.label
    instance_id = instance.pk

    for webhook in webhooks:
        send_webhook_request_async.delay(
            webhook.url,
            model_label,
            instance_id,
            webhook.secret,
            webhook.id
        )