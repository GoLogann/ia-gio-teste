import requests
import logging
from resources.whatsapp.config import WHATSAPP_PHONEID, WHATSAPP_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_whatsapp_template_message(phone_number: str, template_name: str, language_code: str):
    url = f"https://graph.facebook.com/v20.0/197548720118848/messages"

    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }

    data = {
        'messaging_product': 'whatsapp',
        'to': phone_number,
        'type': 'template',
        'template': {
            'name': 'hello_world',
            'language': {
                'code': 'en_US'
            }
        }
    }

    logger.info(f"Enviando template para: {phone_number}")
    logger.info(f"URL: {url}")
    logger.info(f"Cabeçalhos: {headers}")
    logger.info(f"Dados da Requisição: {data}")

    try:
        response = requests.post(url, headers=headers, json=data)
        logger.info(f"Status da Resposta: {response.status_code}")
        logger.info(f"Resposta da API: {response.text}")

        response.raise_for_status()

        return response.json()
    except requests.RequestException as e:
        logger.error(f"Erro ao enviar template para {phone_number}: {e}")
        return {"error": str(e)}
