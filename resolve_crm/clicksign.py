import base64
import decimal
import json
import logging
import os
import requests

from datetime import datetime, timedelta

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
            "content_base64": content_base64,  # prefixo mime + base64
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
        return document_data
    else:
        logger.error("Erro ao criar o documento: %s", response.text)
        return {
            "status": "error",
            "message": "Failed to create document.",
            "response": response.json(),
        }
