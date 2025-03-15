import mimetypes

import httpx
from fastapi.logger import logger

from resources.whatsapp.config import WHATSAPP_TOKEN, WHATSAPP_PHONEID


async def send_message_to_whatsapp(to: str, message: str):
    url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONEID}/messages"
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            logger.info("Mensagem enviada com sucesso!")
        else:
            logger.error(f"Erro ao enviar mensagem: {response.text}")

async def upload_media(file_path: str):
    url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONEID}/media"
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
    }

    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        raise Exception(f"Não foi possível determinar o tipo MIME para o arquivo: {file_path}")

    with open(file_path, 'rb') as file:
        files = {
            'file': (file_path, file, mime_type),
            'messaging_product': (None, 'whatsapp'),
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, files=files)
            if response.status_code == 200:
                return response.json()['id']
            else:
                raise Exception(f"Erro ao fazer upload: {response.text}")

async def send_media_message(to: str, media_id: str, media_type: str):
    url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONEID}/messages"
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": media_type,
        media_type: {"id": media_id}  # "image" ou "video"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            logger.info("Mídia enviada com sucesso!")
        else:
            logger.error(f"Erro ao enviar mídia: {response.text}")

async def send_template_message(to: str, template_name: str):
    url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONEID}/messages"
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "pt_BR"}
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            logger.info("Template Message enviada com sucesso!")
        else:
            logger.error(f"Erro ao enviar Template Message: {response.text}")
            raise Exception(f"Erro ao enviar Template Message: {response.text}")