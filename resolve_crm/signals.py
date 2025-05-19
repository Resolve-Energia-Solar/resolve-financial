from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import requests
import sys
from django.contrib.contenttypes.models import ContentType
from .task import generate_project_number, remove_tag_from_sale
from core.utils import create_process
from resolve_crm.task import (
    check_projects_and_update_sale_tag,
    update_or_create_sale_tag,
)
from .models import Project, Sale
from core.models import Attachment, Process, ProcessBase, SystemConfig, Webhook
import logging
from django.db import transaction


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Project)
def post_create_project(sender, instance, created, **kwargs):
    if not instance.project_number:
        generate_project_number.delay(instance.pk)


@receiver(post_save, sender=Attachment)
def attachment_changed(sender, instance, **kwargs):
    if instance.document_type and any(
        key in instance.document_type.name
        for key in ["CPF", "RG", "Contrato", "CNH", "homologador"]
    ):
        if hasattr(instance.content_object, "projects"):
            annotated = Project.objects.filter(
                pk__in=instance.content_object.projects.all()
            ).with_is_released_to_engineering()
            if annotated.exists():
                for project in annotated:
                    if project.is_released_to_engineering:
                        update_or_create_sale_tag.delay(
                            project.sale.id, project.sale.status
                        )
                    else:
                        remove_tag_from_sale.delay(
                            project.sale.id, "documentação parcial"
                        )


@receiver(post_save, sender=Sale)
def handle_sale_post_save(sender, instance, created, **kwargs):
    print(f"📌 Signal: Venda salva - ID: {instance.id} - Criada: {created}")

    def on_commit_all_tasks():

        annotated = Project.objects.filter(
            sale=instance
        ).with_is_released_to_engineering()

        if not annotated.exists():
            print(f"📌 Signal: Venda não possui projetos - ID: {instance.id}")
            return

        if annotated.filter(is_released_to_engineering=True).exists():
            update_or_create_sale_tag.delay(instance.id, instance.status)
        elif annotated.filter(is_released_to_engineering=False).exists():
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
    annotated = (
        Project.objects.filter(pk=instance.pk).with_is_released_to_engineering().first()
    )

    if annotated and annotated.is_released_to_engineering:
        update_or_create_sale_tag.delay(annotated.sale.id, annotated.sale.status)
