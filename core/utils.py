from copy import deepcopy
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from core.models import Process, ProcessBase

def create_process(
    process_base_id,
    content_type_id,
    object_id,
    nome=None,
    descricao=None,
    user_id=None,
    completion_date=None
):
    with transaction.atomic():
        base = ProcessBase.objects.get(id=process_base_id)

        base_step = base.steps or []
        reset_step = []

        for i, step in enumerate(base_step):
            new_step = deepcopy(step)

            new_step["is_completed"] = False
            new_step["completion_date"] = None
            new_step["user_id"] = None

            if i == 0 and user_id and completion_date:
                new_step["is_completed"] = True
                new_step["completion_date"] = completion_date
                new_step["user_id"] = user_id

            reset_step.append(new_step)

        new_process = Process.objects.create(
            name=nome or f"Processo - {base.name}",
            description=descricao or base.description,
            content_type=ContentType.objects.get(id=content_type_id),
            object_id=object_id,
            deadline=base.deadline,
            steps=reset_step
        )

        return new_process.id



def get_model_data(instance):
    data = {}
    fields_to_skip = {'arquivo_grande', 'campo_muito_longo'}

    for field in instance._meta.get_fields():
        field_name = field.name
        if field_name in fields_to_skip:
            continue

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
