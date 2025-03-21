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
    update_clicksign_document,
    create_signer,
    add_envelope_requirements,
    activate_envelope,
    send_notification,
)
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_or_create_sale_tag(sale_id, sale_status):
    logger.info(f"📌 Task: Atualizando tag para sale {sale_id} com status {sale_status}")
    try:
        sale = Sale.objects.get(id=sale_id)
        sale_ct = ContentType.objects.get_for_model(Sale)
        
        if sale_status == "EA":
            new_tag = "documentação parcial"
            color = "#FF0000"
            tag_qs = Tag.objects.filter(content_type=sale_ct, object_id=sale.id, tag=new_tag)
            if not tag_qs.exists():
                Tag.objects.create(
                    content_type=sale_ct,
                    object_id=sale.id,
                    tag=new_tag,
                    color=color
                )
                logger.info(f"📌 Tag criada para sale {sale.id}")
            else:
                logger.info(f"📌 Tag já existe para sale {sale.id}")
        else:
            tag_qs = Tag.objects.filter(content_type=sale_ct, object_id=sale.id, tag="documentação parcial")
            if tag_qs.exists():
                tag_qs.delete()
                logger.info(f"📌 Tag removida para sale {sale.id}")

    except Sale.DoesNotExist:
        logger.error(f"📌Sale com ID {sale_id} não encontrada.")
        return
    

@shared_task
def remove_tag_from_sale(sale_id, tag_name):
    try:
        sale = Sale.objects.get(id=sale_id)
        logger.info(f"📌 Task: Removendo tag {tag_name} da sale {sale.contract_number}")
        sale_ct = ContentType.objects.get_for_model(Sale)
        tag_qs = Tag.objects.filter(content_type=sale_ct, object_id=sale.id, tag=tag_name)
        if tag_qs.exists():
            tag_qs.delete()
            logger.info(f"📌 Tag removida para sale {sale.id}")
        else:
            logger.info(f"📌 Tag não encontrada para sale {sale.id}")
    except Sale.DoesNotExist:
        logger.error(f"📌Sale com ID {sale_id} não encontrada.")
        return


@shared_task
def check_projects_and_update_sale_tag(sale_id, sale_status):
    try:
        sale = Sale.objects.get(id=sale_id)
        logger.info(f"📌 Task: Verificando projetos da venda {sale.contract_number}")
        for project in sale.projects.all():
            if project.is_released_to_engineering():
                logger.info(f"📌 Task: Projeto {project.id} liberado para engenharia.")
                update_or_create_sale_tag.delay(sale.id, sale_status)
                break
            else:
                logger.info(f"📌 Task: Projeto {project.id} não liberado para engenharia.")
                remove_tag_from_sale.delay(sale.id, "documentação parcial")
                
    except Sale.DoesNotExist:
        logger.error(f"📌Sale com ID {sale_id} não encontrada.")


@shared_task
def send_contract_to_clicksign(sale_id, pdf_content):
    try:
        sale = Sale.objects.get(id=sale_id)
    except Sale.DoesNotExist:
        return {"status": "error", "message": f"Sale {sale_id} não encontrada."}

    # Verifica se já existe um envio anterior para atualizar
    existing_submission = ContractSubmission.objects.filter(sale=sale).first()
    if existing_submission:
        envelope_id = existing_submission.envelope_id
        # Atualiza o documento do envelope
        document_response = update_clicksign_document(
            envelope_id,
            existing_submission.key_number,
            sale.contract_number,
            sale.customer,
            existing_submission.request_signature_key,
            pdf_content
        )
        if document_response.get("status") == "error":
            return {"status": "error", "message": f"Erro ao atualizar documento no envelope: {document_response}"}
        document_key = document_response.get("new_document_id")
        if not document_key:
            return {"status": "error", "message": "Chave do documento ausente após atualização."}

        # Atualiza os dados da submissão existente
        existing_submission.key_number = document_key
        existing_submission.submit_datetime = timezone.now()
        existing_submission.due_date = timezone.now() + datetime.timedelta(days=7)
        existing_submission.save()

        # Envia notificação (opcional)
        notif_response = send_notification(envelope_id)
        if notif_response.get("status") != "success":
            return {"status": "error", "message": "Erro ao enviar notificação após atualização do documento."}

        return {"status": "success", "submission_id": existing_submission.id}

    # Fluxo de criação de envelope, documento, signatário e requisitos (novo envio)
    envelope_response = create_clicksign_envelope(sale.contract_number, sale.customer.complete_name)
    if envelope_response.get("status") != "success":
        return {"status": "error", "message": "Erro ao criar envelope no Clicksign."}
    envelope_id = envelope_response.get("envelope_id")

    document_response = create_clicksign_document(
        envelope_id,
        sale.contract_number,
        sale.customer.complete_name,
        pdf_content
    )
    if document_response.get("status") == "error":
        return {"status": "error", "message": f"Erro ao criar documento no envelope: {document_response}"}
    document_data = document_response.get("data", {})
    document_key = document_data.get("id")
    if not document_key:
        return {"status": "error", "message": "Chave do documento ausente."}

    signer_response = create_signer(envelope_id, sale.customer)
    if signer_response.get("status") != "success":
        return {"status": "error", "message": "Erro ao criar signatário."}
    signer_key = signer_response.get("signer_key")

    req_response = add_envelope_requirements(envelope_id, document_key, signer_key)
    if req_response.get("status") != "success":
        return {"status": "error", "message": "Erro ao adicionar requisitos ao envelope."}

    activate_response = activate_envelope(envelope_id)
    if activate_response.get("status") != "success":
        return {"status": "error", "message": "Erro ao ativar envelope."}

    notif_response = send_notification(envelope_id)
    if notif_response.get("status") != "success":
        return {"status": "error", "message": "Erro ao enviar notificação."}

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


@shared_task
def save_all_sales():
    sales = Sale.objects.all()
    logger.info(f"📌 Task: Salvando todas as vendas.")
    for sale in sales:
        sale.save()
    return {"status": "success", "message": "Vendas salvas com sucesso."}