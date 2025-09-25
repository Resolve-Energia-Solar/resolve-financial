from celery import shared_task
import os, requests, logging
from financial.models import FinancialRecord
from financial.views import OmieIntegrationView
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def send_to_omie_task(record_id):
    try:
        record = FinancialRecord.objects.get(id=record_id)
    except FinancialRecord.DoesNotExist:
        logger.error(f"Registro {record_id} não encontrado.")
        return {"status": "error", "message": "Record not found"}

    omie_service = OmieIntegrationView()
    if (
        record.integration_code is None
        and record.responsible_status == "A"
        and record.payment_status == "P"
    ):
        result = omie_service.create_payment_request(
            record, "Aprovado", record.responsible_notes
        )
        if result.get("codigo_status") != "0":
            logger.error(
                f"Erro ao enviar o registro {record.protocol}: {result.get('descricao_status')}"
            )
            return {
                "status": "error",
                "message": f"Integration error: {result.get('descricao_status')}",
            }
        else:
            record.integration_code = result.get("codigo_lancamento_integracao")
            record.save()
            logger.info(f"Registro {record.protocol} enviado com sucesso.")
            return {"status": "success", "message": "Record sent to Omie successfully"}
    else:
        logger.warning(
            f"Registro {record.protocol} não atende aos critérios para envio."
        )
        return {"status": "warning", "message": "Record does not meet sending criteria"}

@shared_task
def resend_approval_request_to_responsible_task(record_id):
    try:
        record = FinancialRecord.objects.get(id=record_id)
    except FinancialRecord.DoesNotExist:
        logger.error(f"Registro {record_id} não encontrado.")
        return {"status": "error", "message": "Record not found"}

    cancel_url = os.environ.get("CANCEL_FINANCIAL_RECORD_APPROVAL_URL")
    if cancel_url and record.responsible_request_integration_code:
        logger.info(
            f"Cancelando o pedido de aprovação do registro {record.protocol}."
        )
        body = {"run_id": record.responsible_request_integration_code}
        cancel_response = requests.post(cancel_url, json=body)
        logger.info(
            f"Cancel approval request response: {cancel_response.status_code} - {cancel_response.text}"
        )
    else:
        logger.warning(
            "CANCEL_FINANCIAL_RECORD_APPROVAL_URL não está definido nas variáveis de ambiente."
        )

    omie_service = OmieIntegrationView()
    if record.responsible_status == "P":
        supplier_info = omie_service.get_supplier(record.client_supplier_code)
        if supplier_info:
            supplier_name = supplier_info.get("razao_social")
            supplier_cpf = supplier_info.get("cnpj_cpf")
            if supplier_name and supplier_cpf:
                webhook_body = {
                    "id": record.id,
                    "manager_email": record.responsible.email,
                    "description": (
                        f"Registro de Pagamento - nº {record.protocol}\n"
                        f"Criado em {record.created_at.strftime('%d/%m/%Y %H:%M:%S')}\n"
                        f"Valor: {record.value}\n"
                        f"Fornecedor: {supplier_name} ({supplier_cpf})"
                    ),
                }
                webhook_url = os.getenv("FINANCIAL_RECORD_APPROVAL_URL")
                headers = {"Content-Type": "application/json"}
                try:
                    response = requests.post(
                        webhook_url, json=webhook_body, headers=headers
                    )
                    response.raise_for_status()
                    logger.info(
                        f"Convite reenviado para o gestor do registro {record.protocol}."
                    )
                    integration_code = response.headers.get("x-ms-workflow-run-id")
                    if integration_code:
                        record.responsible_request_integration_code = integration_code
                        record.save()
                        logger.info(
                            f"Registro {record.protocol} atualizado com o código de integração: {integration_code}"
                        )
                    return {"status": "success", "message": f"Approval request resent{', previously canceled' if integration_code else ''}"}
                except requests.RequestException as e:
                    logger.error(
                        f"Erro ao enviar webhook para o registro {record.protocol}: {e}"
                    )
                    return {"status": "error", "message": f"Webhook error: {str(e)}"}
            else:
                logger.error(
                    f"Informações do fornecedor incompletas para o registro {record.protocol}."
                )
                return {
                    "status": "error",
                    "message": "Incomplete supplier information from Omie",
                }
        else:
            logger.error(
                f"Erro ao obter informações do fornecedor para o registro {record.protocol}."
            )
            return {"status": "error", "message": "Failed to get supplier information"}
    else:
        logger.warning(f"Registro {record.protocol} não está em status 'Pendente'.")
        return {"status": "warning", "message": "Record not in 'Pending' status"}


@shared_task
def notify_requester_on_audit_change_task(record_id):
    try:
        record = FinancialRecord.objects.get(id=record_id)
    except FinancialRecord.DoesNotExist:
        logger.error(f"Registro {record_id} não encontrado para notificação ao solicitante.")
        return {"status": "error", "message": "Record not found"}

    if record.audit_status not in ("C", "R"):
        logger.info(
            f"Registro {record.protocol} não está em status de cancelamento/reprovação para notificação."
        )
        return {"status": "ignored", "message": "Audit status is not C or R"}

    # Exigir motivo para cancelamento/reprovação
    if not (record.audit_notes and record.audit_notes.strip()):
        logger.info(
            f"Notificação não enviada para {record.protocol} por ausência de motivo (audit_notes)."
        )
        return {"status": "ignored", "message": "Missing reason (audit_notes)"}

    requester = getattr(record, "requester", None)
    requester_email = getattr(requester, "email", None)
    if not requester or not requester_email:
        logger.warning(
            f"Solicitante ou e-mail ausente para o registro {record.protocol}. Notificação não enviada."
        )
        return {"status": "warning", "message": "Requester email not available"}

    status_text = "Cancelada" if record.audit_status == "C" else "Reprovada"
    subject = f"Sua solicitação {record.protocol} foi {status_text}"

    notes = record.audit_notes or "—"
    try:
        requester_name = getattr(requester, "first_name", None) or getattr(
            requester, "complete_name", ""
        )
    except Exception:
        requester_name = ""

    # Datas e formatos
    local_created_at = timezone.localtime(record.created_at) if record.created_at else None
    local_audit_date = timezone.localtime(record.audit_response_date) if record.audit_response_date else None

    context = {
        'status_text': status_text,
        'requester_name': requester_name,
        'protocol': record.protocol,
        'value': f"R$ {record.value:.2f}",
        'created_at': local_created_at.strftime('%d/%m/%Y %H:%M') if local_created_at else None,
        'audit_by': getattr(record.audit_by, 'complete_name', None) or getattr(record.audit_by, 'email', None) or '—',
        'audit_date': local_audit_date.strftime('%d/%m/%Y %H:%M') if local_audit_date else '—',
        'notes': notes,
        'requesting_department': getattr(record.requesting_department, 'name', None) or '—',
        'category_name': record.category_name,
        'client_supplier_name': record.client_supplier_name,
        'due_date': record.due_date.strftime('%d/%m/%Y') if record.due_date else '—',
        'payment_method': record.get_payment_method_display() if hasattr(record, 'get_payment_method_display') else '—',
    }

    html_content = render_to_string('financial/audit-notification-email.html', context)

    try:
        email = EmailMessage(subject=subject, body=html_content, to=[requester_email])
        email.content_subtype = "html"
        email.send()
        logger.info(
            f"Notificação de {status_text.lower()} enviada para o solicitante do registro {record.protocol}."
        )
        return {"status": "success", "message": "Notification email sent"}
    except Exception as e:
        logger.error(
            f"Erro ao enviar notificação ao solicitante do registro {record.protocol}: {e}",
            exc_info=True,
        )
        return {"status": "error", "message": f"Failed to send email: {e}"}
