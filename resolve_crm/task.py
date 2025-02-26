from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from core.models import Tag
from resolve_crm.models import Sale

@shared_task
def update_or_create_sale_tag(sale_id):
    try:
        sale = Sale.objects.get(id=sale_id)
        sale_ct = ContentType.objects.get_for_model(Sale)

        if sale.status == "F":
            tag_qs = Tag.objects.filter(content_type=sale_ct, object_id=sale.id, tag="documentação parcial")
            if tag_qs.exists():
                tag_qs.delete()
        else:
            new_tag = "documentação parcial"
            color = "#FF0000"

            tag_qs = Tag.objects.filter(content_type=sale_ct, object_id=sale.id, tag="documentação parcial")
            if not tag_qs.exists():
                Tag.objects.create(
                    content_type=sale_ct,
                    object_id=sale.id,
                    tag=new_tag,
                    color=color
                )
    except Sale.DoesNotExist:
        print(f"⚠️ Sale com ID {sale_id} não encontrada.")

@shared_task
def check_projects_and_update_sale_tag(sale_id):
    from .models import Project

    try:
        sale = Sale.objects.get(id=sale_id)
        for project in sale.projects.all():
            if project.is_released_to_engineering():
                update_or_create_sale_tag.delay(sale.id)  # Chama a outra tarefa no Celery
                break
    except Sale.DoesNotExist:
        print(f"⚠️ Sale com ID {sale_id} não encontrada.")
