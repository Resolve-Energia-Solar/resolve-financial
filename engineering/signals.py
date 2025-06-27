from django.db.models.signals import post_save
from django.dispatch import receiver
from engineering.models import RequestsEnergyCompany


@receiver(post_save, sender=RequestsEnergyCompany)
def update_project_status(sender, instance, **kwargs):
    if instance.status == "D" and instance.type.name == "Vistoria Final":
        instance.project.status = "CO"

    instance.project.save()