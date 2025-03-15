from fastapi import APIRouter, Depends, Query, HTTPException
from qdrant_client import QdrantClient

from sqlalchemy.orm import Session
from starlette import status

from constantes_globais.apiuri import CHATBOT_URI_V2
from constantes_globais.enum.tipo_dialogo import PROMPT_ENXAME
from controller.v2.dialogo_controller import _execute_service
from database.database import get_db
from database.qdrant_db import get_qdrant_client
from dataprovider.api.session_handler import end_session
from domain.schemas.dialogo_schema import DialogoListHistory
from domain.schemas.gio_schema import ComunicacaoEnxameContatoSchema
from repository.dialogo_repository import DialogoRepository
from services.chatbot_service import ChatBotService
from services.dialogo_service import DialogoService
from utils.helpers import extract_roteiro_from_html, processar_parametros

swarn_webchat_public_router = APIRouter()

chatbot_service = ChatBotService()

@swarn_webchat_public_router.post(CHATBOT_URI_V2 + "/swarm/web-chat", status_code=status.HTTP_200_OK)
async def webchat_swarm(
        gio: ComunicacaoEnxameContatoSchema,
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client),
):
    modelo = ""
    if gio.modelo_ata_formatado:
        modelo = extract_roteiro_from_html(gio.modelo_ata_formatado)

    roteiro = {
        "id_comunicacao_enxame_contato": gio.id,
        "id_departamento": gio.id_departamento,
        "id_usuario": gio.id_usuario,
        "questao": gio.questao,
        "nome": gio.nome,
        "telefone": gio.telefone,
        "email": gio.email,
        "modelo": modelo,
    }

    return  await chatbot_service.web_chat_enxame(gio, roteiro, db, qdrant_client)

@swarn_webchat_public_router.post(CHATBOT_URI_V2 + "/swarm/list-dialogue-history", status_code=status.HTTP_200_OK)
def list_dialog_swarm(
        request: DialogoListHistory,
        db: Session = Depends(get_db),
):
    """
    Endpoint to list the dialogue history of the swarm web chat with pagination and sorting.
    """
    repository = DialogoRepository(db)
    dialog = repository.get_last_dialogo_with_detalhes_by_user_id(request.idUsuario)

    if not dialog:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=f"Dialog not found for user"
        )

    return dialog

@swarn_webchat_public_router.post(CHATBOT_URI_V2 + "/swarm/finish-webchat-session", status_code=status.HTTP_200_OK)
def finish_webchat_session_swarm(id_usuario: str = Query(..., alias="idUsuario")):
    """
    Endpoint para finalizar sessão na Gio criativa.
    """
    try:
        end_session(id_usuario)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

    return {"data": "Sessão finalizada"}