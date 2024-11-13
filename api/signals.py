from engineering.models import Units
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Units)
def check_unit_status(sender, instance, created, **kwargs):
    # Evitar recursão
    if getattr(instance, '_skip_post_save', False):
        return

    # Verifica se o estado de change_owner precisa ser atualizado
    if instance.project is not None:
        if instance.project.homologator and instance.name:
            bill_name = instance.name.lower()
            project_homologator = instance.project.homologator.complete_name.lower()
            if bill_name == project_homologator:
                change_owner = False
            else:
                change_owner = True
                
            # Atualiza apenas se houver mudança
            if instance.change_owner != change_owner:
                instance.change_owner = change_owner
                instance._skip_post_save = True
                instance.save(update_fields=['change_owner'])

