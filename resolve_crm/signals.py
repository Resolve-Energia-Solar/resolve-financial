from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import requests
import sys
from django.contrib.contenttypes.models import ContentType
from .task import generate_project_number, remove_tag_from_sale
from core.utils import create_process
from resolve_crm.task import check_projects_and_update_sale_tag, update_or_create_sale_tag
from .models import Project, Sale
from core.models import Attachment, Process, ProcessBase, SystemConfig,Webhook
import logging
from django.db import transaction


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
    data = {}
    for field in instance._meta.get_fields():
        field_name = field.name

        try:
            field_value = getattr(instance, field_name, None)
        except Exception:
            continue

        if field.one_to_many or field.many_to_many:
            field_value = [obj.id for obj in field_value.all()] if field_value else []
        elif field.is_relation:
            field_value = field_value.id if field_value else None
        elif hasattr(field_value, 'url'):
            field_value = field_value.url if field_value else None
        elif hasattr(field_value, 'isoformat'):
            field_value = field_value.isoformat()

        data[field_name] = field_value

    return data


@receiver(post_save, sender=Project)
def post_create_project(sender, instance, created, **kwargs):
    if not instance.project_number:
        generate_project_number.delay(instance.pk)


@receiver(post_save)
def send_webhook_on_save(sender, instance, created, **kwargs):
    if 'migrate' in sys.argv or 'test' in sys.argv:
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


@receiver(post_save, sender=Attachment)
def attachment_changed(sender, instance, **kwargs):
    if instance.document_type and any(
        key in instance.document_type.name for key in ['CPF', 'RG', 'Contrato', 'CNH', 'homologador']
    ):
        if hasattr(instance.content_object, 'projects'):
            sale = instance.content_object
            check_projects_and_update_sale_tag.delay(sale.id, sale.status)


@receiver(post_save, sender=Sale)
def handle_sale_post_save(sender, instance, created, **kwargs):
    print(f"📌 Signal: Venda salva - ID: {instance.id} - Criada: {created}")
    def on_commit_all_tasks():
        
        annotated = (
            Project.objects
            .filter(sale=instance)
            .with_is_released_to_engineering()
        )
        
        if not annotated.exists():
            print(f"📌 Signal: Venda não possui projetos - ID: {instance.id}")
            return
        
        if annotated.filter(is_released_to_engineering=True).exists():
            print(f"📌 Signal: Venda possui projetos liberados para engenharia - ID: {instance.id}")
            update_or_create_sale_tag.delay(instance.id, instance.status)
        elif annotated.filter(is_released_to_engineering=False).exists():
            print(f"📌 Signal: Venda não possui projetos liberados para engenharia - ID: {instance.id}")
            remove_tag_from_sale.delay(instance.id, "documentação parcial")
        
        # print(f"📌 Entrando na Func")
        # check_projects_and_update_sale_tag.delay(instance.id, instance.status)
        
        # if not instance.signature_date:
        #     return
        
        # try:
        #     system_config = SystemConfig.objects.get()
        #     default_process = system_config.configs.get('default_process')
        #     print(f"📌 Signal: default_process - {default_process}")
        # except SystemConfig.DoesNotExist:
        #     logger.error("Configuração do sistema não encontrada.")
        #     return

        # try:
        #     modelo = ProcessBase.objects.get(name__exact=default_process)
        #     print(f"📌 Signal: modelo - {modelo}")
        # except ProcessBase.DoesNotExist:
        #     return

        # projects = Project.objects.filter(sale=instance)
        # if not projects.exists():
        #     return

        # content_type = ContentType.objects.get_for_model(Project)
        # project_ids = list(projects.values_list('id', flat=True))
        # existing_processes = set(
        #     Process.objects.filter(
        #         content_type=content_type,
        #         object_id__in=project_ids
        #     ).values_list('object_id', flat=True)
        # )

        # for project in projects:
        #     if project.id in existing_processes:
        #         continue
            
        #     create_process(
        #         process_base_id=modelo.id,
        #         content_type_id=content_type.id,
        #         object_id=project.id,
        #         nome=f"Processo {modelo.name} {instance.contract_number} - {instance.customer.complete_name}",
        #         descricao=modelo.description,
        #         user_id=instance.customer.id if instance.customer else None,
        #         completion_date=instance.signature_date.isoformat(),
        #     )

    transaction.on_commit(on_commit_all_tasks)
    

@receiver(post_save, sender=Project)
def project_changed(sender, instance, **kwargs):
    print(f"📌 Signal: Projeto salvo - ID: {instance.id}")
    annotated = (
        Project.objects
        .filter(pk=instance.pk)
        .with_is_released_to_engineering()
        .first()
    )

    if annotated and annotated.is_released_to_engineering:
        update_or_create_sale_tag.delay(annotated.sale.id, annotated.sale.status)
