import logging
import os
import requests
from django.conf import settings
from celery import shared_task

from .models import Ticket

logger = logging.getLogger(__name__)
session = requests.Session()


@shared_task
def send_ticket_info_to_teams(ticket_id: int) -> dict[str, str]:
    """Envia notificação ao Microsoft Teams ao criar ou atualizar um ticket."""
    webhook_url = os.environ.get("TICKET_INFO_WEBHOOK_URL")
    if not webhook_url:
        msg = "Webhook do Teams não configurado."
        logger.error(msg)
        return {"status": "error", "message": msg}

    ticket = (
        Ticket.objects.select_related(
            "created_by",
            "responsible",
            "subject",
            "project__sale__customer",
            "ticket_type",
        )
        .filter(id=ticket_id)
        .first()
    )
    if not ticket:
        msg = f"Ticket {ticket_id} não encontrado."
        logger.warning(msg)
        return {"status": "error", "message": msg}

    def safe(path: str, default: str) -> str:
        obj = ticket
        for attr in path.split("."):
            obj = getattr(obj, attr, None)
            if obj is None:
                return default
        return str(obj)

    payload = {
        "protocol": safe("protocol", "Sem protocolo"),
        "requester_name": safe("created_by.complete_name", "Sem solicitante"),
        "requester_email": safe("created_by.email", "Sem solicitante"),
        "responsible_name": safe("responsible.complete_name", "Sem responsável"),
        "responsible_email": safe("responsible.email", "Sem responsável"),
        "title": safe("subject.subject", "Sem assunto"),
        "project": (
            f"{ticket.project.project_number} – {safe('project.sale.customer.complete_name', '')}"
            if ticket.project
            else "Sem projeto, cliente ou venda"
        ),
        "type": safe("ticket_type.name", "Sem tipo"),
        "status": ticket.get_status_display(),
        "urgency": ticket.get_priority_display(),
        "description": safe("description", "Sem descrição"),
    }

    logger.info("Enviando payload ao Teams: %s", payload)
    try:
        response = session.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Falha ao enviar ticket %s ao Teams: %s", ticket_id, e)
        return {"status": "error", "message": str(e)}

    logger.info("Notificação enviada com sucesso para o Teams.")
    return {"status": "success", "message": "Notificação enviada para o Teams."}
