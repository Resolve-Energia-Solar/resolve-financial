from copy import deepcopy
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from core.models import Process, ProcessBase

def criar_processo_from_modelo(
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
        
        etapas_base = base.steps or []
        etapas_zeradas = []

        for i, etapa in enumerate(etapas_base):
            etapa_copia = deepcopy(etapa)

            etapa_copia["is_completed"] = False
            etapa_copia["completion_date"] = None
            etapa_copia["user_id"] = None

            if i == 0 and user_id and completion_date:
                etapa_copia["is_completed"] = True
                etapa_copia["completion_date"] = completion_date.isoformat()
                etapa_copia["user_id"] = user_id

            etapas_zeradas.append(etapa_copia)

        novo_processo = Process.objects.create(
            name=nome or f"Processo - {base.name}",
            description=descricao or base.description,
            content_type=ContentType.objects.get(id=content_type_id),
            object_id=object_id,
            deadline=base.deadline,
            steps=etapas_zeradas
        )

        return novo_processo
