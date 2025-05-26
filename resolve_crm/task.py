import datetime
import logging
import os
from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.db import connection, transaction
from django.utils import timezone
import requests
import math
from django.conf import settings
from accounts.models import Branch
from core.models import Tag
from logistics.models import SaleProduct

from .clicksign import (
    activate_envelope,
    add_envelope_requirements,
    create_clicksign_document,
    create_clicksign_envelope,
    create_signer,
    send_notification,
    update_clicksign_document,
)
from .models import ContractSubmission, Project, Sale

logger = logging.getLogger(__name__)


@shared_task
def generate_sale_contract_number(sale_id):
    table = Sale._meta.db_table
    lock_name = "contract_number_lock"

    with connection.cursor() as cursor:
        cursor.execute("SELECT GET_LOCK(%s, 10)", [lock_name])
        try:
            cursor.execute(
                f"""
                SELECT MAX(CAST(SUBSTRING(contract_number, 6) AS UNSIGNED))
                FROM {table}
                WHERE contract_number LIKE 'RESOL%%'
            """
            )
            last = cursor.fetchone()[0] or 0
            new = last + 1
            # agora usando zfill para 6 dígitos
            new_cn = f"RESOL{str(new).zfill(6)}"

            cursor.execute(
                f"UPDATE {table} SET contract_number = %s WHERE id = %s",
                [new_cn, sale_id],
            )
        finally:
            cursor.execute("SELECT RELEASE_LOCK(%s)", [lock_name])

    return ("success", f"Contract number {new_cn} generated for sale {sale_id}.")


@shared_task
def generate_project_number(project_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT GET_LOCK('project_number_lock', 10)")
        try:
            cursor.execute(
                """
              SELECT MAX(CAST(SUBSTRING(project_number,5) AS UNSIGNED))
              FROM resolve_crm_project
              WHERE project_number NOT LIKE '%ProjMig%'
            """
            )
            last = cursor.fetchone()[0] or 0
            new = last + 1
            proj_num = f"PROJ{new:02}"
            cursor.execute(
                "UPDATE resolve_crm_project SET project_number=%s WHERE id=%s",
                [proj_num, project_id],
            )
        finally:
            cursor.execute("SELECT RELEASE_LOCK('project_number_lock')")

        return (
            "success",
            f"Project number {proj_num} generated for project {project_id}.",
        )


@shared_task
def generate_project_number_for_all():
    projects = Project.objects.filter(project_number__isnull=True)
    for project in projects:
        generate_project_number.delay(project.id)

    return ("success", f"Project numbers generated for all projects.")


@shared_task
def update_or_create_sale_tag(sale_id, sale_status):
    logger.info(
        f"📌 Task: Atualizando tag para sale {sale_id} com status {sale_status}"
    )
    try:
        sale = Sale.objects.get(id=sale_id)
        sale_ct = ContentType.objects.get_for_model(Sale)

        if sale_status == "EA":
            new_tag = "documentação parcial"
            color = "#FF0000"
            tag_qs = Tag.objects.filter(
                content_type=sale_ct, object_id=sale.id, tag=new_tag
            )
            if not tag_qs.exists():
                Tag.objects.create(
                    content_type=sale_ct, object_id=sale.id, tag=new_tag, color=color
                )
                logger.info(f"📌 Tag criada para sale {sale.id}")
            else:
                logger.info(f"📌 Tag já existe para sale {sale.id}")
        else:
            tag_qs = Tag.objects.filter(
                content_type=sale_ct, object_id=sale.id, tag="documentação parcial"
            )
            if tag_qs.exists():
                tag_qs.delete()
                logger.info(f"📌 Tag removida para sale {sale.id}")

        return (
            "success",
            f"Tag {new_tag} atualizada para venda {sale.contract_number} com sucesso.",
        )

    except Sale.DoesNotExist:
        logger.error(f"📌Sale com ID {sale_id} não encontrada.")
        return ("error", f"Sale com ID {sale_id} não encontrada.")


@shared_task
def remove_tag_from_sale(sale_id, tag_name):
    try:
        sale = Sale.objects.get(id=sale_id)
        logger.info(f"📌 Task: Removendo tag {tag_name} da sale {sale.contract_number}")
        sale_ct = ContentType.objects.get_for_model(Sale)
        tag_qs = Tag.objects.filter(
            content_type=sale_ct, object_id=sale.id, tag=tag_name
        )
        if tag_qs.exists():
            tag_qs.delete()
            logger.info(f"📌 Tag removida para sale {sale.id}")
        else:
            logger.info(f"📌 Tag não encontrada para sale {sale.id}")

        return (
            "success",
            f"Tag {tag_name} removida da venda {sale.contract_number} com sucesso.",
        )

    except Sale.DoesNotExist:
        logger.error(f"📌Sale com ID {sale_id} não encontrada.")
        return ("error", f"Sale com ID {sale_id} não encontrada.")


@shared_task
def check_projects_and_update_sale_tag(sale_id, sale_status):
    try:
        sale = Sale.objects.get(pk=sale_id)
    except Sale.DoesNotExist:
        logger.error(f"📌 Sale com ID {sale_id} não encontrada.")
        return ("error", f"Sale com ID {sale_id} não encontrada.")

    logger.info(f"📌 Task: Verificando projetos da venda {sale.contract_number}")

    # usa o annotate definido em ProjectQuerySet
    projects = sale.projects.with_is_released_to_engineering()

    for project in projects:
        if project.is_released_to_engineering:
            logger.info(f"📌 Projeto {project.id} liberado para engenharia.")
            update_or_create_sale_tag.delay(sale.id, sale_status)
            break
        else:
            logger.info(f"📌 Projeto {project.id} não liberado para engenharia.")
            remove_tag_from_sale.delay(sale.id, "documentação parcial")

    return ("success", f"Tag atualizada para venda {sale.contract_number} com sucesso.")


@shared_task
def send_clicksign_url_to_teams(customer_name, seller_name, clicksign_url):
    """
    Send a notification to Microsoft Teams when a contract is available for signature.

    Args:
        customer_name: Name of the customer who will sign the contract
        seller_name: Name of the seller associated with the contract
        clicksign_url: URL to the Clicksign document

    Returns:
        dict: Status and message of the operation
    """
    webhook_url = os.environ.get("TEAMS_CLICKSIGN_WEBHOOK_URL")

    if not webhook_url:
        logger.error("Webhook do Teams não configurado. Mensagem não enviada.")
        return {"status": "error", "message": "Webhook do Teams não configurado."}

    payload = {
        "customer": customer_name,
        "seller": seller_name,
        "clicksign_url": clicksign_url,
    }

    logger.info(f"📌 Task: Enviando mensagem para o Teams")

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Mensagem enviada para o Teams com sucesso.")
        return {"status": "success", "message": "Mensagem enviada para o Teams."}
    except requests.RequestException as e:
        logger.error(f"Erro ao enviar mensagem para o Teams: {str(e)}")
        return {"status": "error", "message": f"Erro ao enviar mensagem: {str(e)}"}


@shared_task
def send_contract_to_clicksign(sale_id, pdf_content):
    try:
        sale = Sale.objects.get(id=sale_id)
    except Sale.DoesNotExist:
        return {"status": "error", "message": f"Sale {sale_id} não encontrada."}

    existing_submission = (
        ContractSubmission.objects.filter(sale=sale).order_by("-id").first()
    )
    # Tenta atualizar se já existe
    if existing_submission:
        envelope_id = existing_submission.envelope_id
        document_response = update_clicksign_document(
            envelope_id,
            existing_submission.key_number,
            sale.contract_number,
            sale.customer,
            sale.seller.complete_name,
            existing_submission.request_signature_key,
            pdf_content,
        )
        # Em caso de erro, anula existing_submission para cair no fluxo de criação
        if document_response.get("status") == "error":
            logger.warning(
                "Erro ao atualizar documento, criando novo envelope", document_response
            )
            existing_submission = None
        else:
            document_key = document_response.get("new_document_id")
            if not document_key:
                logger.warning(
                    "Chave do documento ausente após atualização, criando novo envelope"
                )
                existing_submission = None
            else:
                # segue fluxo de atualização normal...
                existing_submission.key_number = document_key
                existing_submission.submit_datetime = timezone.now()
                existing_submission.due_date = timezone.now() + datetime.timedelta(
                    days=7
                )
                existing_submission.save()
                notif_response = send_notification(envelope_id)
                if notif_response.get("status") != "success":
                    return {
                        "status": "error",
                        "message": "Erro ao enviar notificação após atualização.",
                    }
                # envia link ao Teams...
                try:
                    from .task import send_clicksign_url_to_teams

                    send_clicksign_url_to_teams.delay(
                        customer_name=sale.customer.complete_name,
                        seller_name=sale.seller.complete_name,
                        clicksign_url=f"https://app.clicksign.com/widget/notarial/{existing_submission.request_signature_key}/documents/{document_key}",
                    )
                except Exception as e:
                    logger.error("Erro ao enviar link para o Teams", str(e))
                return {"status": "success", "submission_id": existing_submission.id}

    # --- fluxo de criação de envelope (novo envio) ---
    envelope_response = create_clicksign_envelope(
        sale.contract_number, sale.customer.complete_name, sale.seller.complete_name
    )
    if envelope_response.get("status") != "success":
        return {"status": "error", "message": "Erro ao criar envelope no Clicksign."}
    envelope_id = envelope_response["envelope_id"]

    document_response = create_clicksign_document(
        envelope_id, sale.contract_number, sale.customer.complete_name, pdf_content
    )
    if document_response.get("status") == "error":
        return {
            "status": "error",
            "message": f"Erro ao criar documento no envelope: {document_response}",
        }
    document_data = document_response.get("data", {})
    document_key = document_data.get("id")
    if not document_key:
        return {"status": "error", "message": "Chave do documento ausente."}

    signer_response = create_signer(envelope_id, sale.customer)
    if signer_response.get("status") != "success":
        return {"status": "error", "message": "Erro ao criar signatário."}
    signer_key = signer_response["signer_key"]

    req_response = add_envelope_requirements(envelope_id, document_key, signer_key)
    if req_response.get("status") != "success":
        return {
            "status": "error",
            "message": "Erro ao adicionar requisitos ao envelope.",
        }

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
        link=f"https://app.clicksign.com/envelopes/{envelope_id}",
    )

    try:
        from .task import send_clicksign_url_to_teams

        send_clicksign_url_to_teams.delay(
            customer_name=sale.customer.complete_name,
            seller_name=sale.seller.complete_name,
            clicksign_url=f"https://app.clicksign.com/widget/notarial/{signer_key}/documents/{document_key}",
        )
    except Exception as e:
        logger.error("Erro ao enviar link para o Teams", str(e))

    logger.info(f"📌 Task concluída. ID da submissão: {submission.id}")
    return {"status": "success", "submission_id": submission.id}


@shared_task
def save_all_sales():
    sales = Sale.objects.all()
    logger.info(f"📌 Task: Salvando todas as vendas.")
    for sale in sales:
        sale.save()
    return {"status": "success", "message": "Vendas salvas com sucesso."}


@shared_task
def create_projects_for_sale(sale_id):
    sale_products = SaleProduct.objects.filter(sale_id=sale_id)
    project_instances = [
        Project(sale_id=sale_id, product=sp.product) for sp in sale_products
    ]
    if project_instances:
        Project.objects.bulk_create(project_instances)

    return {"status": "success", "message": f"Projetos criados para a venda {sale_id}."}


def _linear_distance_km(lat1, lon1, lat2, lon2):
    """
    Haversine fallback caso a API do Google retorne ZERO_RESULTS.
    """
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return R * c

@shared_task
def update_project_delivery_type(project_id):
    logger.info(f"🔄 Iniciando cálculo de delivery_type por rota para Project {project_id}")
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        logger.warning(f"Project {project_id} não encontrado")
        return

    matriz = Branch.objects.filter(name__icontains="Matriz").first()
    proj_addr = project.address  # cached_property

    if not (matriz and matriz.address and proj_addr):
        logger.error(f"Endereço da Matriz ou do Projeto {project_id} ausente")
        return

    # extrai e valida coordenadas
    try:
        lat1 = float(matriz.address.latitude)
        lon1 = float(matriz.address.longitude)
        lat2 = float(proj_addr.latitude)
        lon2 = float(proj_addr.longitude)
    except (TypeError, ValueError) as e:
        logger.error(f"Coordenadas inválidas para Project {project_id}: {e}")
        return

    # chama Google Distance Matrix
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins":      f"{lat1},{lon1}",
        "destinations": f"{lat2},{lon2}",
        "mode":         "driving",
        "key":          settings.GMAPS_API_KEY,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        elm = resp.json()["rows"][0]["elements"][0]
    except Exception as e:
        logger.error(f"Erro chamando Google API: {e}")
        elm = {"status": "ZERO_RESULTS"}

    # se a API retornar OK, usa distance.value; senão fallback Haversine
    if elm.get("status") == "OK":
        dist_km = elm["distance"]["value"] / 1000.0
        logger.info(f"Distância de rota (Google): {dist_km:.2f} km")
    else:
        dist_km = _linear_distance_km(lat1, lon1, lat2, lon2)
        logger.info(f"ZERO_RESULTS → fallback linear: {dist_km:.2f} km")

    # atualiza delivery_type
    project.delivery_type = "D" if dist_km > 200 else "C"
    project.save(update_fields=["delivery_type"])
    logger.info(
        f"Project {project_id} delivery_type atualizado para "
        f"{project.delivery_type} ({dist_km:.2f} km)"
    )

    return {
        "status": "success",
        "project_id": project_id,
        "delivery_type": project.delivery_type,
        "distance_km": round(dist_km, 2),
    }
