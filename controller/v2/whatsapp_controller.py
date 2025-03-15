from fastapi import APIRouter, Request

from constantes_globais.apiuri import WHATSAPP_URI_V2
from domain.schemas.message_request import MessageRequest
from services.whatsapp_service import WhatsAppService
from services.chatbot_service import ChatBotService

whatsapp_service = WhatsAppService()
chatbot_service = ChatBotService()

whatsapp_router = APIRouter()

@whatsapp_router.get(WHATSAPP_URI_V2)
async def get_webhook(request: Request):
    """
    Verifica o webhook do WhatsApp para confirmar a assinatura.
    """
    return await whatsapp_service.verify_webhook(request)

@whatsapp_router.post(WHATSAPP_URI_V2)
async def post_webhook(request: Request):
    """
    Processa mensagens recebidas via webhook do WhatsApp.
    """
    return await whatsapp_service.process_webhook(request, chatbot_service)

@whatsapp_router.post(WHATSAPP_URI_V2 + "/send-message")
async def post_send_message(request: MessageRequest):
    """
    Envia uma mensagem via WhatsApp para um número especificado.
    """
    await whatsapp_service.enviar_mensagem(request.to, request.message)
    return {"status": "message sent"}
