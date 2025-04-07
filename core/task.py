# core/tasks.py

from celery import shared_task
from copy import deepcopy
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from core.models import Process, ProcessBase

@shared_task(bind= True , max_retries= 3 , default_retry_delay= 5 * 60) 
def create_process_async(
    self,
    process_base_id,
    content_type_id,
    object_id,
    nome=None,
    descricao=None,
    user_id=None,
    completion_date=None
):
    with transaction.atomic():
        print(f"Creating process asynchronously for object ID: {object_id}")
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
        
        print(f"Process created with ID: {new_process.id}")

        return new_process.id
