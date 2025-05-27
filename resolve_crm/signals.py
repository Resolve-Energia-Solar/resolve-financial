from django.db.models.signals import post_save
from django.dispatch import receiver

from engineering.models import Units
from .task import (
    generate_project_number,
    generate_sale_contract_number,
    remove_tag_from_sale,
    update_project_delivery_type,
)
from resolve_crm.task import (
    update_or_create_sale_tag,
)
from .models import Project, Sale
from core.models import Attachment
import logging
from django.db import transaction

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Project)
def post_create_project(sender, instance, created, **kwargs):
    if not instance.project_number:
        generate_project_number.delay(instance.pk)
    
    if not instance.delivery_type:
        update_project_delivery_type.delay(instance.id)
        

@receiver(post_save, sender=Units)
def post_units(sender, instance, created, **kwargs):
    if instance.address and instance.main_unit and instance.project:
        update_project_delivery_type.delay(instance.project.id)


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
    if not instance.contract_number:
        generate_sale_contract_number.delay(instance.id)
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

    transaction.on_commit(on_commit_all_tasks)


@receiver(post_save, sender=Project)
def project_changed(sender, instance, **kwargs):
    annotated = (
        Project.objects.filter(pk=instance.pk).with_is_released_to_engineering().first()
    )

    if annotated and annotated.is_released_to_engineering:
        update_or_create_sale_tag.delay(annotated.sale.id, annotated.sale.status)
