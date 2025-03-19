import base64
import decimal
import json
import logging
import os
import requests

from datetime import datetime, timedelta
from resolve_crm.models import Sale

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = os.environ.get("CLICKSIGN_API_URL")
ACCESS_TOKEN = os.environ.get("CLICKSIGN_ACCESS_TOKEN")


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


def create_clicksign_envelope(sale_number, customer_name):
    if not API_URL or not ACCESS_TOKEN:
        logger.error("API_URL ou ACCESS_TOKEN não configurados.")
        return {"status": "error", "message": "API_URL or ACCESS_TOKEN not configured."}

    url = f"{API_URL}/api/v3/envelopes"
    payload = {
        "data": {
            "type": "envelopes",
            "attributes": {
                "name": f"CONTRATO-{sale_number}-{customer_name}",
                "locale": "pt-BR",
                "auto_close": True,
                "block_after_refusal": True,
                "deadline_at": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S-03:00"),
                "default_subject": "Contrato de Venda de Sistema Fotovoltaico - Resolve Energia Solar",
                "default_message": "Olá! O seu contrato está disponível para assinatura. Acesse o link para assinar."
            }
        }
    }

    headers = {
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json",
        "Authorization": f"{ACCESS_TOKEN}"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        if response.status_code == 201:
            envelope_id = response.json()["data"]["id"]
            logger.info(json.dumps({
                "message": f"Envelope {envelope_id} criado com sucesso!",
                "envelope_id": envelope_id
            }))
            return {"status": "success", "envelope_id": envelope_id}
        else:
            error_detail = response.json().get("errors", [{}])[0].get("detail", "Erro desconhecido.")
            logger.error(f"Erro ao criar o envelope: {error_detail}")
            return {
                "status": "error",
                "message": f"Failed to create envelope: {error_detail}",
                "response": response.content,
            }
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição", str(e))
        return {"status": "error", "message": f"RequestException: {str(e)}"}


def create_clicksign_document(envelope_id, sale_number, customer_name, pdf_bytes):
    if not API_URL or not ACCESS_TOKEN:
        logger.error("API_URL ou ACCESS_TOKEN não configurados.")
        return {"status": "error", "message": "API_URL or ACCESS_TOKEN not configured."}

    try:
        if not pdf_bytes:
            logger.error("PDF está vazio (0 bytes).", "O PDF gerado está vazio.")
            return {"status": "error", "message": "O PDF gerado está vazio (0 bytes)."}

        document_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
        content_base64 = f"data:application/pdf;base64,{document_base64}"

    except Exception as e:
        logger.error("Erro ao converter documento para base64", str(e))
        return {"status": "error", "message": f"Base64ConversionError: {str(e)}"}

    document_name = f"CONTRATO-{sale_number}-{customer_name}.pdf"
    payload = {
        "data": {
            "type": "documents",
            "attributes": {
                "filename": document_name,
                "content_base64": content_base64,
                "metadata": {
                    "sale_number": sale_number,
                    "customer_name": customer_name
                }
            }
        }
    }

    try:
        response = requests.post(
            f"{API_URL}/api/v3/envelopes/{envelope_id}/documents",
            headers={
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
                "Authorization": f"{ACCESS_TOKEN}"
            },
            data=json.dumps(payload),
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição", str(e))
        return {
            "status": "error",
            "message": f"RequestException: {str(e)}",
        }

    if response.status_code == 201:
        document_data = response.json()
        logger.info(json.dumps({
            "message": "Documento criado com sucesso!",
            "status": "success",
            "document_data": document_data
        }))
        sale = Sale.objects.filter(contract_number=sale_number).first()
        if not sale:
            logger.error("Sale not found for contract number", sale_number)
            return {
                "status": "error",
                "message": f"Sale not found for contract number: {sale_number}",
            }
        return document_data
    else:
        error_detail = response.json().get("errors", [{}])[0].get("detail", "Erro desconhecido.")
        logger.error(f"Erro ao criar o documento: {error_detail}")
        return {
            "status": "error",
            "message": f"Failed to create document: {error_detail}",
            "response": response.json(),
        }


def create_signer(envelope_id, customer):
    url = f"{API_URL}/api/v3/envelopes/{envelope_id}/signers"
    
    phone_number = customer.phone_numbers.filter(is_main=True).first()
    if not phone_number:
        logger.error("Número de telefone principal não encontrado para o cliente", "Telefone principal ausente")
        return {
            "status": "error",
            "message": "Número de telefone principal não encontrado para o cliente.",
        }

    formatted_phone_number = f'{phone_number.area_code}{phone_number.phone_number}'
    if len(formatted_phone_number) != 11:
        logger.error("Número de telefone principal está em um formato inválido", formatted_phone_number)
        return {
            "status": "error",
            "message": "Número de telefone principal está em um formato inválido.",
        }

    formatted_documentation = f"{str(customer.first_document)[:3]}.{str(customer.first_document)[3:6]}.{str(customer.first_document)[6:9]}-{str(customer.first_document)[9:11]}"
    
    payload = {
        "data": {
            "type": "signers",
            "attributes": {
                "name": customer.complete_name,
                "birthday": customer.birth_date.strftime("%Y-%m-%d"),
                "email": customer.email,
                "phone_number": formatted_phone_number,
                "has_documentation": True,
                "documentation": formatted_documentation,
                "refusable": True,
                "communicate_events": {
                    "document_signed": "email",
                    "signature_request": "whatsapp",
                    "signature_reminder": "email"
                }
            }
        }
    }

    headers = {
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json",
        "Authorization": f"{ACCESS_TOKEN}"
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        if response.status_code == 201:
            signer_response = response.json()
            logger.info(json.dumps({
                "message": "Signatário criado com sucesso!",
                "status": "success",
                "signer_id": signer_response['data']['id']
            }))
            return {"status": "success", "signer_key": signer_response["data"]["id"]}
        else:
            error_detail = response.json().get("errors", [{}])[0].get("detail", "Erro desconhecido.")
            logger.error(f"Erro ao criar o signatário: {error_detail}")
            return {
                "status": "error",
                "message": f"Failed to create signer: {error_detail}",
                "response": response.content,
            }
    except requests.exceptions.HTTPError as e:
        logger.error("Erro na requisição", str(e))
        if response.content:
            logger.error(f"Detalhes do erro: {response.content.decode('utf-8')}")
        return {
            "status": "error",
            "message": f"HTTPError: {str(e)}",
            "response": response.content.decode("utf-8") if response.content else "",
        }
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição", str(e))
        return {"status": "error", "message": f"RequestException: {str(e)}"}


def add_envelope_requirements(envelope_id, document_id, signer_id):
    url = f"{API_URL}/api/v3/envelopes/{envelope_id}/bulk_requirements"
    
    payload = {
        "atomic:operations": [
            {
                "op": "add",
                "data": {
                    "type": "requirements",
                    "attributes": {
                        "action": "agree",
                        "role": "contractor"
                    },
                    "relationships": {
                        "document": {
                            "data": {"type": "documents", "id": document_id}
                        },
                        "signer": {
                            "data": {"type": "signers", "id": signer_id}
                        }
                    }
                }
            },
            {
                "op": "add",
                "data": {
                    "type": "requirements",
                    "attributes": {
                        "action": "provide_evidence",
                        "auth": "selfie"
                    },
                    "relationships": {
                        "document": {
                            "data": {"type": "documents", "id": document_id}
                        },
                        "signer": {
                            "data": {"type": "signers", "id": signer_id}
                        }
                    }
                }
            },
            {
                "op": "add",
                "data": {
                    "type": "requirements",
                    "attributes": {
                        "action": "provide_evidence",
                        "auth": "official_document"
                    },
                    "relationships": {
                        "document": {
                            "data": {"type": "documents", "id": document_id}
                        },
                        "signer": {
                            "data": {"type": "signers", "id": signer_id}
                        }
                    }
                }
            }
        ]
    }

    headers = {
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json",
        "Authorization": f"{ACCESS_TOKEN}"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 201:
            try:
                error_data = response.json()
                errors = error_data.get("errors", [])
                for error in errors:
                    logger.error(f"Erro do Clicksign: {error.get('detail', 'Erro desconhecido')}")
            except Exception as parse_err:
                logger.error(f"Falha ao decodificar JSON de erro: {str(parse_err)}")
            response.raise_for_status()
        
        logger.info("Requisitos adicionados com sucesso via bulk_requirements.")
        return {"status": "success", "message": "Requisitos adicionados com sucesso."}
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição: " + str(e))
        return {"status": "error", "message": f"RequestException: {str(e)}"}


def activate_envelope(envelope_id):
    url = f"{API_URL}/api/v3/envelopes/{envelope_id}/"

    payload = {
        "data": {
            "id": envelope_id,
	        "type": "envelopes",
            "attributes": {
                "status": "running"
            }
        }
    }

    headers = {
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json",
        "Authorization": f"{ACCESS_TOKEN}"
    }

    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()

        if response.status_code == 200:
            logger.info(json.dumps({
                "message": "Envelope ativado com sucesso!",
                "status": "success"
            }))
            return {"status": "success", "message": "Envelope ativado com sucesso."}
        else:
            error_detail = response.json().get("errors", [{}])[0].get("detail", "Erro desconhecido.")
            logger.error(f"Erro ao ativar o envelope: {error_detail}")
            return {
                "status": "error",
                "message": f"Failed to activate envelope: {error_detail}",
                "response": response.content,
            }
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição", str(e))
        return {"status": "error", "message": f"RequestException: {str(e)}"}


def send_notification(envelope_id, message="Olá! O contrato está disponível para assinatura. Acesse o link para assinar."):
    url = f"{API_URL}/api/v3/envelopes/{envelope_id}/notifications"

    payload = {
        "data": {
            "type": "notifications",
            "attributes": {
                "message": message
            }
        }
    }

    headers = {
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json",
        "Authorization": f"{ACCESS_TOKEN}"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        if response.status_code == 201:
            return {"status": "success", "message": "Notificação enviada com sucesso."}
        else:
            error_detail = response.json().get("errors", [{}])[0].get("detail", "Erro desconhecido.")
            return {
                "status": "error",
                "message": f"Failed to send notification: {error_detail}",
                "response": response.content,
            }
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição", str(e))
        return {"status": "error", "message": f"RequestException: {str(e)}"}


def update_clicksign_document(envelope_id, document_id, sale_number, customer, signer_id, pdf_bytes):
    if not API_URL or not ACCESS_TOKEN:
        logger.error("API_URL ou ACCESS_TOKEN não configurados.")
        return {"status": "error", "message": "API_URL or ACCESS_TOKEN not configured."}

    try:
        document_content = pdf_bytes
        if not document_content:
            logger.warning("PDF está vazio (0 bytes).", "O PDF gerado está vazio.")
            return {"status": "error", "message": "O PDF gerado está vazio (0 bytes)."}
        document_base64 = base64.b64encode(document_content).decode("utf-8")
        content_base64 = f"data:application/pdf;base64,{document_base64}"
    except Exception as e:
        logger.error("Erro ao converter documento para base64", str(e))
        return {"status": "error", "message": f"Base64ConversionError: {str(e)}"}

    headers = {
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json",
        "Authorization": f"{ACCESS_TOKEN}"
    }

    # Adiciona o novo documento
    document_name = f"CONTRATO-{sale_number}-{customer.complete_name}.pdf"
    add_document_url = f"{API_URL}/api/v3/envelopes/{envelope_id}/documents"
    add_document_payload = {
        "data": {
            "type": "documents",
            "attributes": {
                "filename": document_name,
                "content_base64": content_base64,
                "metadata": {
                    "sale_number": sale_number,
                    "customer_name": customer.complete_name
                }
            }
        }
    }

    try:
        add_document_response = requests.post(add_document_url, headers=headers, json=add_document_payload)
        add_document_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        if add_document_response.status_code == 403:
            error_detail = add_document_response.json().get("errors", [{}])[0].get("detail", "Erro desconhecido.")
            logger.error(f"Erro ao adicionar o novo documento: {error_detail}")
            return {"status": "error", "message": f"Forbidden: {error_detail}"}
        logger.error("Erro ao adicionar o novo documento", str(e))
        return {"status": "error", "message": f"RequestException: {str(e)}"}

    if add_document_response.status_code == 201:
        document_data = add_document_response.json()
        logger.info(json.dumps({
            "message": "Novo documento adicionado com sucesso!",
            "status": "success",
            "new_document_id": document_data["data"]["id"]
        }))
        new_document_id = document_data["data"]["id"]
    else:
        error_detail = add_document_response.json().get("errors", [{}])[0].get("detail", "Erro desconhecido.")
        logger.error(f"Erro ao adicionar o novo documento: {error_detail}")
        return {"status": "error", "message": f"Failed to add new document: {error_detail}"}

    # Vincula o signatário existente ao novo documento usando bulk_requirements
    add_requirements_response = add_envelope_requirements(envelope_id, new_document_id, signer_id)
    if add_requirements_response.get("status") != "success":
        logger.error("Erro ao adicionar requisitos ao envelope", add_requirements_response)
        return {"status": "error", "message": "Erro ao adicionar requisitos ao envelope."}

    # Cancela o documento antigo
    cancel_url = f"{API_URL}/api/v3/envelopes/{envelope_id}/documents/{document_id}"
    cancel_payload = {
        "data": {
            "type": "documents",
            "id": document_id,
            "attributes": {
                "status": "canceled"
            }
        }
    }
    try:
        cancel_response = requests.patch(cancel_url, headers=headers, json=cancel_payload)
        cancel_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        if cancel_response.status_code == 403:
            error_detail = cancel_response.json().get("errors", [{}])[0].get("detail", "Erro desconhecido.")
            logger.error(f"Erro ao cancelar o documento: {error_detail}")
            return {"status": "error", "message": f"Forbidden: {error_detail}"}
        logger.error("Erro ao cancelar o documento", str(e))
        return {"status": "error", "message": f"RequestException: {str(e)}"}

    if cancel_response.status_code != 200:
        error_detail = cancel_response.json().get("errors", [{}])[0].get("detail", "Erro desconhecido.")
        logger.error(f"Erro ao cancelar o documento: {error_detail}")
        return {"status": "error", "message": f"Failed to cancel the old document: {error_detail}"}

    logger.info(json.dumps({
        "message": f"Documento antigo cancelado com sucesso! Novo documento ID: {new_document_id}",
        "status": "success",
        "new_document_id": new_document_id
    }))
    return {"status": "success", "new_document_id": new_document_id}
