from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from core.models import Tag
from celery import shared_task
from django.utils import timezone
import datetime
from resolve_crm.models import Sale, ContractSubmission
from resolve_crm.clicksign import (
    create_clicksign_envelope,
    create_clicksign_document,
    create_signer,
    add_envelope_requirements,
    activate_envelope,
    send_notification,
)


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
        pass
        # logger.error(f"Venda com ID {sale_id} não encontrada.")

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


@shared_task
def send_contract_to_clicksign(sale_id, pdf_content):
    """
    Task que envia o contrato para o Clicksign de forma assíncrona.
    Recebe o ID da venda e o conteúdo PDF do contrato (em bytes).
    """
    try:
        sale = Sale.objects.get(id=sale_id)
    except Sale.DoesNotExist:
        return {"status": "error", "message": f"Sale {sale_id} não encontrada."}

    # Cria o envelope no Clicksign
    envelope_response = create_clicksign_envelope(sale.contract_number, sale.customer.complete_name)
    if envelope_response.get("status") != "success":
        return {"status": "error", "message": "Erro ao criar envelope no Clicksign."}
    envelope_id = envelope_response.get("envelope_id")

    # Adiciona o documento (PDF) ao envelope
    document_response = create_clicksign_document(envelope_id, sale.contract_number, sale.customer.complete_name, pdf_content)
    if document_response.get("status") == "error":
        return {"status": "error", "message": f"Erro ao criar documento no envelope: {document_response}"}
    document_data = document_response.get("data", {})
    document_key = document_data.get("id")
    if not document_key:
        return {"status": "error", "message": "Chave do documento ausente."}

    # Cria o signatário para o envelope
    signer_response = create_signer(envelope_id, sale.customer)
    if signer_response.get("status") != "success":
        return {"status": "error", "message": "Erro ao criar signatário."}
    signer_key = signer_response.get("signer_key")

    # Adiciona os requisitos ao envelope
    req_response = add_envelope_requirements(envelope_id, document_key, signer_key)
    # Verifica se todos os requisitos foram adicionados com sucesso
    for req in req_response:
        if req.get("status") != "success":
            return {"status": "error", "message": "Erro ao adicionar requisitos ao envelope."}

    # Ativa o envelope
    activate_response = activate_envelope(envelope_id)
    if activate_response.get("status") != "success":
        return {"status": "error", "message": "Erro ao ativar envelope."}

    # Envia a notificação
    notif_response = send_notification(envelope_id)
    if notif_response.get("status") != "success":
        return {"status": "error", "message": "Erro ao enviar notificação."}

    # Cria o registro de ContractSubmission
    submission = ContractSubmission.objects.create(
        sale=sale,
        request_signature_key=signer_key,
        key_number=document_key,
        envelope_id=envelope_id,
        status="P",
        submit_datetime=timezone.now(),
        due_date=timezone.now() + datetime.timedelta(days=7),
        link=f"https://app.clicksign.com/envelopes/{envelope_id}"
    )
    return {"status": "success", "submission_id": submission.id}