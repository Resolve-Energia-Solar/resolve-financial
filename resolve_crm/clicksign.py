import base64
import decimal
import json
import logging
import os
import requests

from datetime import datetime, timedelta, timezone

from resolve_crm.models import ContractSubmission, Sale

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = os.environ.get("CLICKSIGN_API_URL")
ACCESS_TOKEN = os.environ.get("CLICKSIGN_ACCESS_TOKEN")


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


def create_clicksign_document(sale_number, customer_name, pdf_bytes):
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
    deadline_at = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S-03:00")

    payload = {
        "document": {
            "path": f"/{document_name}",
            "content_base64": content_base64,
            "deadline_at": deadline_at,
            "auto_close": True,
            "locale": "pt-BR",
            "sequence_enabled": False,
            "block_after_refusal": True,
        },
    }

    # Fazer a requisição
    try:
        response = requests.post(
            f"{API_URL}/api/v1/documents?access_token={ACCESS_TOKEN}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição: %s", e)
        # response.text só existe depois da requisição, verifique se está acessível
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

        return document_data, document_data["document"]["key"]
    else:
        logger.error("Erro ao criar o documento: %s", response.text)
        return {
            "status": "error",
            "message": "Failed to create document.",
            "response": response.json(),
        }

def create_signer(customer):
    url = f"{API_URL}/api/v1/signers?access_token={ACCESS_TOKEN}"
    
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

    payload = {
        "signer": {
            "email": customer.email,
            "phone_number": formatted_phone_number,
            "auths": ['whatsapp'],
            "name": customer.complete_name,
            "has_documentation": True,
            "selfie_enabled": True,
            "handwritten_enabled": False,
            "location_required_enabled": False,
            "official_document_enabled": True,
            "liveness_enabled": False,
            "facial_biometrics_enabled": False,
        }
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        if response.status_code == 201:
            signer_response = response.json()
            logger.info("Signatário criado com sucesso!")
            logger.info(f"ID do Signatário: {signer_response['signer']['key']}")
            return {"status": "success", "signer_key": signer_response["signer"]["key"]}
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

def create_document_signer(key_number, signer_key, sale):
    url = f"{API_URL}/api/v1/lists?access_token={ACCESS_TOKEN}"

    payload = {
        "list": {
            "document_key": key_number,
            "signer_key": signer_key,
            "sign_as": "contractor"
        }
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        if response.status_code == 201:
            list_data = response.json()
            doc_signer = list_data["list"]

            # Criação da instância de ContractSubmission
            submission = ContractSubmission.objects.create(
                sale=sale,
                key_number=key_number,
                request_signature_key=doc_signer["request_signature_key"],
                status="P",
                submit_datetime=datetime.now(tz=timezone.utc),
                due_date=datetime.now(tz=timezone.utc) + timedelta(days=7),
                link=doc_signer['url'],
            )

            return submission  # Retorne a instância em vez de um dicionário

        return {
            "status": "error",
            "message": "Falha ao associar signatário ao documento.",
            "response": response.content,
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao associar signatário: {e}")
        return {"status": "error", "message": f"RequestException: {str(e)}"}

def send_notification(submission):
    url_email = f"{API_URL}/api/v1/notifications?access_token={ACCESS_TOKEN}"
    url_whatsapp = f"{API_URL}/api/v1/notify_by_whatsapp?access_token={ACCESS_TOKEN}"
    
    payload_email = {
        "notification": {
            "request_signature_key": submission.key_number,
            "url": submission.link,
            "message": "Olá! O contrato está disponível para assinatura. Acesse o link para assinar.",
        }
    }
    
    payload_whatsapp = {
        "notification": {
            "request_signature_key": submission.key_number
        }
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        # Send email notification
        response_email = requests.post(url_email, headers=headers, json=payload_email)
        response_email.raise_for_status()
        
        # Send WhatsApp notification
        response_whatsapp = requests.post(url_whatsapp, headers=headers, json=payload_whatsapp)
        response_whatsapp.raise_for_status()
        
        if response_email.status_code == 201 and response_whatsapp.status_code == 201:
            return {"status": "success", "message": "Notifications sent successfully."}
        else:
            return {
                "status": "error",
                "message": "Failed to send one or more notifications.",
                "response_email": response_email.content,
                "response_whatsapp": response_whatsapp.content,
            }
    except requests.exceptions.RequestException as e:
        logger.error("Erro na requisição: %s", e)
        return {"status": "error", "message": f"RequestException: {str(e)}"}
