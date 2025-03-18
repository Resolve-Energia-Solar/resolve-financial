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
            logger.info(f"Envelope {envelope_id} criado com sucesso!")
            return {"status": "success", "envelope_id": envelope_id}
        else:
            logger.error("Erro ao criar o envelope: %s", response.content)
            return {
                "status": "error",
                "message": "Failed to create envelope.",
                "response": response.content,
            }
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição: %s", e)
        return {"status": "error", "message": f"RequestException: {str(e)}"}

def create_clicksign_document(envelope_id, sale_number, customer_name, pdf_bytes):
    if not API_URL or not ACCESS_TOKEN:
        logger.error("API_URL ou ACCESS_TOKEN não configurados.")
        return {"status": "error", "message": "API_URL or ACCESS_TOKEN not configured."}

    try:
        # pdf_bytes já é o conteúdo binário do PDF
        document_content = pdf_bytes  
        # Verifica se está vazio
        if not document_content:
            logger.error("PDF está vazio (0 bytes).")
            return {"status": "error", "message": "O PDF gerado está vazio (0 bytes)."}

        # Converte para Base64
        document_base64 = base64.b64encode(document_content).decode("utf-8")

        # Inclui o prefixo de mime type
        content_base64 = f"data:application/pdf;base64,{document_base64}"

    except Exception as e:
        logger.error("Erro ao converter documento para base64: %s", e)
        return {"status": "error", "message": f"Base64ConversionError: {str(e)}"}
    
    # Montar o payload...
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

    # Fazer a requisição
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
        logger.error("Erro na requisição: %s", e)
        return {
            "status": "error",
            "message": f"RequestException: {str(e)}",
        }

    if response.status_code == 201:
        document_data = response.json()
        logger.info("Documento criado com sucesso!")
        sale = Sale.objects.filter(contract_number=sale_number).first()
        if not sale:
            logger.error("Sale not found for contract number: %s", sale_number)
            return {
                "status": "error",
                "message": f"Sale not found for contract number: {sale_number}",
            }
        return document_data
    else:
        logger.error("Erro ao criar o documento: %s", response.text)
        return {
            "status": "error",
            "message": "Failed to create document.",
            "response": response.json(),
        }

def create_signer(envelope_id, customer):
    url = f"{API_URL}/api/v3/envelopes/{envelope_id}/signers"
    
    phone_number = customer.phone_numbers.filter(is_main=True).first()
    if not phone_number:
        logger.error("Número de telefone principal não encontrado para o cliente.")
        return {
            "status": "error",
            "message": "Número de telefone principal não encontrado para o cliente.",
        }

    formatted_phone_number = f'{phone_number.area_code}{phone_number.phone_number}'
    if len(formatted_phone_number) != 11:
        logger.error("Número de telefone principal está em um formato inválido.")
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
                "group": "3",
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
            logger.info("Signatário criado com sucesso!")
            logger.info(f"ID do Signatário: {signer_response['data']['id']}")
            return {"status": "success", "signer_key": signer_response["data"]["id"]}
        else:
            logger.error("Erro ao criar o signatário: %s", response.content)
            return {
                "status": "error",
                "message": "Failed to create signer.",
                "response": response.content,
            }
    except requests.exceptions.HTTPError as e:
        logger.error("Erro na requisição: %s", e)
        if response.content:
            logger.error("Detalhes do erro: %s", response.content.decode('utf-8'))
        return {
            "status": "error",
            "message": f"HTTPError: {str(e)}",
            "response": response.content.decode("utf-8") if response.content else "",
        }
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição: %s", e)
        return {"status": "error", "message": f"RequestException: {str(e)}"}

def add_envelope_requirements(envelope_id, document_id, signer_id):
    url = f"{API_URL}/api/v3/envelopes/{envelope_id}/requirements"
    
    payloads = [
        {
            "data": {
                "type": "requirements",
                "attributes": {
                    "action": "agree",
                    "role": "contractor"
                },
                "relationships": {
                    "document": {
                        "data": { "type": "documents", "id": document_id }
                    },
                    "signer": {
                        "data": { "type": "signers", "id": signer_id }
                    }
                }
            }
        },
        {
            "data": {
                "type": "requirements",
                "attributes": {
                    "action": "provide_evidence",
                    "auth": "selfie"
                },
                "relationships": {
                    "document": {
                        "data": { "type": "documents", "id": document_id }
                    },
                    "signer": {
                        "data": { "type": "signers", "id": signer_id }
                    }
                }
            }
        },
        {
            "data": {
                "type": "requirements",
                "attributes": {
                    "action": "provide_evidence",
                    "auth": "official_document"
                },
                "relationships": {
                    "document": {
                        "data": { "type": "documents", "id": document_id }
                    },
                    "signer": {
                        "data": { "type": "signers", "id": signer_id }
                    }
                }
            }
        }
    ]

    headers = {
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json",
        "Authorization": f"{ACCESS_TOKEN}"
    }

    results = []
    for payload in payloads:
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            if response.status_code == 201:
                results.append({"status": "success", "message": "Requisito adicionado com sucesso."})
            else:
                logger.error("Erro ao adicionar o requisito: %s", response.content)
                results.append({
                    "status": "error",
                    "message": "Failed to add requirement.",
                    "response": response.content,
                })
        except requests.exceptions.RequestException as e:
            logger.error("Erro na requisição: %s", e)
            results.append({"status": "error", "message": f"RequestException: {str(e)}"})

    return results

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
            logger.info("Envelope ativado com sucesso!")
            return {"status": "success", "message": "Envelope ativado com sucesso."}
        else:
            logger.error("Erro ao ativar o envelope: %s", response.content)
            return {
                "status": "error",
                "message": "Failed to activate envelope.",
                "response": response.content,
            }
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição: %s", e)
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
            return {
                "status": "error",
                "message": "Failed to send notification.",
                "response": response.content,
            }
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição: %s", e)
        return {"status": "error", "message": f"RequestException: {str(e)}"}
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição: %s", e)
        return {"status": "error", "message": f"RequestException: {str(e)}"}
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição: %s", e)
        return {"status": "error", "message": f"RequestException: {str(e)}"}


def update_clicksign_document(envelope_id, document_id, sale_number, customer, pdf_bytes):
    if not API_URL or not ACCESS_TOKEN:
        logger.error("API_URL ou ACCESS_TOKEN não configurados.")
        return {"status": "error", "message": "API_URL or ACCESS_TOKEN not configured."}

    try:
        document_content = pdf_bytes
        if not document_content:
            logger.error("PDF está vazio (0 bytes).")
            return {"status": "error", "message": "O PDF gerado está vazio (0 bytes)."}
        document_base64 = base64.b64encode(document_content).decode("utf-8")
        content_base64 = f"data:application/pdf;base64,{document_base64}"
    except Exception as e:
        logger.error("Erro ao converter documento para base64: %s", e)
        return {"status": "error", "message": f"Base64ConversionError: {str(e)}"}

    headers = {
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json",
        "Authorization": f"{ACCESS_TOKEN}"
    }

    # Agora adiciona o novo documento
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
        logger.error("Erro ao adicionar o novo documento: %s", e)
        return {"status": "error", "message": f"RequestException: {str(e)}"}

    if add_document_response.status_code == 201:
        document_data = add_document_response.json()
        logger.info("Novo documento adicionado com sucesso!")
        new_document_id = document_data["data"]["id"]
    else:
        logger.error("Erro ao adicionar o novo documento: %s", add_document_response.text)
        return {"status": "error", "message": "Failed to add new document.", "response": add_document_response.json()}

    # Vincula o signatário ao novo documento
    signer_response = create_signer(envelope_id, customer)
    if signer_response.get("status") != "success":
        logger.error("Erro ao criar o signatário: %s", signer_response.get("message"))
        return {"status": "error", "message": "Erro ao criar o signatário."}

    signer_key = signer_response.get("signer_key")
    if not signer_key:
        logger.error("Erro ao obter a chave do signatário.")
        return {"status": "error", "message": "Chave do signatário não encontrada."}

    add_requirements_response = add_envelope_requirements(envelope_id, new_document_id, signer_key)
    if any(req.get("status") != "success" for req in add_requirements_response):
        logger.error("Erro ao adicionar requisitos ao envelope.")
        return {"status": "error", "message": "Erro ao adicionar requisitos ao envelope."}

    # Cancelar o documento antigo
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
        logger.error("Erro ao cancelar o documento: %s", e)
        return {"status": "error", "message": f"RequestException: {str(e)}"}

    if cancel_response.status_code != 200:
        logger.error("Erro ao cancelar o documento: %s", cancel_response.text)
        return {"status": "error", "message": "Failed to cancel the old document."}

    logger.info(f"Documento antigo cancelado com sucesso! Novo documento ID: {new_document_id}")
    return {"status": "success", "new_document_id": new_document_id}
