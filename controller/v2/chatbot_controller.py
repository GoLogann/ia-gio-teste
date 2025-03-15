import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends
from sqlalchemy.orm import Session
from starlette import status

from constantes_globais.apiuri import CHATBOT_URI_V2
from database.database import get_db
from domain.schemas.configuracao_modelo_schema import ContextoModelo
from services.chatbot_service import ChatBotService
from services.configuracao_service import ConfiguracaoService
from services.websocket_manager import WebSocketManager
chatbot_router = APIRouter()

chatbot_service = ChatBotService()
socket_manager = WebSocketManager()

@chatbot_router.websocket("/api/v1/ws/{dialogue_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, dialogue_id: str, user_id: str):
    await socket_manager.add_user_to_dialogue(
        dialogue_id=dialogue_id,
        user_id=user_id,
        websocket=websocket
    )

    message = {
        "user_id": user_id,
        "dialogue_id": dialogue_id,
        "message": f"User {user_id} connected to room - {dialogue_id}"
    }

    await socket_manager.broadcast_to_dialogue(
        dialogue_id=dialogue_id,
        message=json.dumps(message)
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = {
                "user_id": user_id,
                "dialogue_id": dialogue_id,
                "message": data
            }
            await socket_manager.broadcast_to_dialogue(dialogue_id=dialogue_id, message=json.dumps(message))

    except WebSocketDisconnect:
        await socket_manager.remove_user_from_dialogue(dialogue_id=dialogue_id, websocket=websocket)

        message = {
            "user_id": user_id,
            "dialogue_id": dialogue_id,
            "message": f"User {user_id} disconnected from room - {dialogue_id}"
        }

        await socket_manager.broadcast_to_dialogue(dialogue_id=dialogue_id, message=json.dumps(message))

@chatbot_router.post(CHATBOT_URI_V2 + "/enviar-midia/{telefone_usuario}")
async def enviar_midia(telefone_usuario: str = None):
    await chatbot_service.enviar_midia(telefone_usuario)


@chatbot_router.get(CHATBOT_URI_V2 + "/get-respostas")
async def get_respostas(
    request: Request,
    id_comunicacao_enxame_contato: str,
):
    """
    Endpoint para recuperar as respostas do usuário associadas a um diálogo com o chatbot WhatsApp.
    """
    response = chatbot_service.get_respostas_usuario(id_comunicacao_enxame_contato, request)
    return response

@chatbot_router.post(CHATBOT_URI_V2 + "/add-llm-model-context", status_code=status.HTTP_201_CREATED)
def add_llm_model_context(
        context: ContextoModelo,
        db: Session = Depends(get_db)
):
    service = ConfiguracaoService(db)

    return service.add_context_to_llm_model(context)