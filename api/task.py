from celery import shared_task
import requests
import logging

logger = logging.getLogger(__name__)

# @shared_task
# def processar_contrato(dados_contrato, token):
#     url = "https://api-externa-assinatura.com/contratos"
#     headers = {"Authorization": token}
#     response = requests.post(url, json=dados_contrato, headers=headers)
#     return response.json()

@shared_task
def processar_contrato(dados_contrato, token):
    logger.info(f"Iniciando processamento do contrato: {dados_contrato}")
    url = "https://api-externa-assinatura.com/contratos"
    headers = {"Authorization": token}
    response = requests.post(url, json=dados_contrato, headers=headers)
    
    if response.status_code == 200:
        print(response.json())
        logger.info(f"Contrato processado com sucesso: {response.json()}")
        return {"status": "sucesso", "detalhes": response.json()}
    else:
        print(response.text)
        logger.error(f"Falha ao processar contrato: {response.text}")
        return {"status": "falha", "erro": response.text}