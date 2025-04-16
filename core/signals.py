from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Process, StepName

@receiver(post_save, sender=Process)
def update_current_steps(sender, instance, created, **kwargs):
    print("Atualizando etapas atuais via signal...")
    
    etapas = instance.steps or []
    concluidas = {et.get("id") for et in etapas if et.get("is_completed")}
    liberadas = []

    for etapa in etapas:
        if etapa.get("is_completed"):
            continue
        dependencias = etapa.get("dependencies", [])
        if all(dep in concluidas for dep in dependencias):
            liberadas.append(etapa)

    print("Etapas liberadas:", liberadas)

    step_ids = []
    for etapa in liberadas:
        step_value = etapa.get("step")
        if isinstance(step_value, dict):
            step_ids.append(step_value.get("id"))
        elif isinstance(step_value, list) and len(step_value) == 2:
            _, step_id = step_value
            step_ids.append(step_id)

    print("IDs das etapas liberadas:", step_ids)

    steps = StepName.objects.filter(id__in=step_ids)
    print("Queryset das etapas liberadas:", steps)

    instance.current_step.set(steps)
    print("Etapas atuais atualizadas com sucesso!")