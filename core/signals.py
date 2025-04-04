from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from core.models import Process, ProcessBase
from core.utils import criar_processo_from_modelo
from resolve_crm.models import Project, Sale

@receiver(post_save, sender=Sale)
def criar_esteira_contrato(sender, instance, created, **kwargs):
    print(f"🔧 Criando esteira de contrato para a venda {instance.id}...")
    print(f"possui signature_date {instance.signature_date}...")

    if not instance.signature_date:
        return

    try:
        modelo = ProcessBase.objects.get(id=1) 
    except ProcessBase.DoesNotExist:
        return

    projects = Project.objects.filter(sale=instance)
    

    for project in projects:
        print(f"🔧 Verificando se o projeto {project.id} já possui processo...")
        print(f"se possui processo: {Process.objects.filter(
            content_type_id=project.content_type_id,
            object_id=project.id
        ).exists()}")
        
        if Process.objects.filter(
            content_type_id=project.content_type_id,
            object_id=project.id
        ).exists():
            continue 

        print(f"🔧 Criando processo para project {project.id} da venda {instance.id}...")

        criar_processo_from_modelo(
            process_base_id=modelo.id,
            content_type_id=project.content_type_id,
            object_id=project.id,
            nome=f"Processo - Venda #{instance.id}",
            descricao=f"Processo gerado automaticamente para a venda com contrato {instance.contract_number} - {instance.customer.get_full_name() if instance.customer else 'Cliente'}",
            user_id=instance.customer.id if instance.customer else None,
            completion_date=instance.signature_date or None
        )
