from celery import shared_task
import os, requests, logging
from financial.models import FinancialRecord
from financial.views import OmieIntegrationView

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
