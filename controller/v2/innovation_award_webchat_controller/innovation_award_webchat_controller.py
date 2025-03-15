import json
import os
from typing import Optional
from redis import Redis
from fastapi import APIRouter, UploadFile, Depends, File, HTTPException, Form, Query
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session
from starlette import status

from constantes_globais.apiuri import CHATBOT_URI_V2
from constantes_globais.enum.contextos import QUESTIONS
from constantes_globais.enum.tipo_dialogo import PROMPT_INNOVATION_AWARD
from controller.v2.dialogo_controller import _execute_service
from database.database import get_db
from database.qdrant_db import get_qdrant_client
from dataprovider.api.session_handler import end_session
from domain.schemas.dialogo_schema import DialogoListHistory
from domain.schemas.gio_schema import GioRequestSchemaInnovationAward
from repository.dialogo_repository import DialogoRepository
from repository.store import QdrantVectorStore
from services.chatbot_service import ChatBotService
from services.chatgpt_handler_dynamic import ChatGPTHandlerDynamic
from services.dialogo_service import DialogoService
from services.document_processor import DocumentProcessor
from services.embedding_service import EmbeddingService
from services.redis_handler_service import RedisHandler
from services.retriever import DocumentRetriever
from services.sentence_transformers import SentenceTransformersEmbeddingClient
from utils.helpers import processar_parametros, process_file_for_rag

innovation_award_router = APIRouter()

chatbot_service = ChatBotService()

@innovation_award_router.post(CHATBOT_URI_V2 + "/innovation-awards/web-chat")
async def webchat_innovation_award(
        gio: str = Form(...),
        file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client),
        redis_client: Redis = Depends(RedisHandler().get_redis_client),
):
    try:
        gio_dict = json.loads(gio)
        gio_obj = GioRequestSchemaInnovationAward.model_validate(gio_dict)
        present_document = False

        redis_key = f"context_project:{gio_obj.user_id}"

        stored_context = redis_client.get(redis_key)
        context_project = json.loads(stored_context) if stored_context else {}

        if file is not None:
            if file.size > 1024 * 1024:
                raise HTTPException(status_code=400, detail="O arquivo deve ter no máximo 1 MB.")
            file_path = f"/tmp/{file.filename}"
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
            try:
                vector_store = QdrantVectorStore()
                retriever = DocumentRetriever(vector_store)
                answer_question = ChatGPTHandlerDynamic()
                embedding_service = EmbeddingService(embedding_client=SentenceTransformersEmbeddingClient())

                document_text = process_file_for_rag(file_path)
                processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
                chunks = processor.process_document_data(document_text)

                chunk_embeddings = embedding_service.generate_embeddings(chunks)

                vector_store.save(
                    collection_name=gio_obj.company_name,
                    user_id=gio_obj.user_id.__str__(),
                    chunks=chunks,
                    chunk_embeddings=chunk_embeddings
                )

                for question in QUESTIONS:
                    query_embedding = embedding_service.embedding_client.embed(question)
                    relevant_docs = retriever.retrieve_relevant_documents(
                        collection_name=gio_obj.company_name,
                        query_embedding=query_embedding,
                    )
                    response, _ = answer_question.generate_answer_based_on_document_for_innovation_award(
                        user_id=gio_obj.user_id.__str__(),
                        question=question,
                        relevant_docs=relevant_docs
                    )

                    context_project[question] = response

                redis_client.set(redis_key, json.dumps(context_project), ex=86400)

                gio_obj.question = (
                                       "O usuário enviou um arquivo com informações sobre seu projeto para candidatura ao premio de inovação. "
                                       "Foram extraídas as respostas para algumas perguntas do roteiro. Analise as perguntas respondidas e as não respondidas "
                                       "para dar sequência ao processo. Caso alguma resposta esteja faltando, pergunte ao usuário. "
                                       "Abaixo estão as perguntas e suas respectivas respostas: \n") + str(
                    context_project)

                present_document = True
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

        return await chatbot_service.webchat_innovation_award(gio_obj, present_document, db, qdrant_client)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@innovation_award_router.post(CHATBOT_URI_V2 + "/innovation-awards/list-dialog-history", status_code=status.HTTP_200_OK)
def list_dialog_innovation_awards(
        request: DialogoListHistory,
        size: int = Query(10, ge=0),
        page: int = Query(0, ge=0),
        sort: str = Query("id DESC"),
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client),
):
    """
    Endpoint to list the dialogue history of the innovation awards web chat with pagination and sorting.
    """

    repository = DialogoRepository(db)
    dialog = repository.get_dialog_by_user_id(request.idUsuario)

    if not dialog:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=f"Dialog not found for user"
        )

    filter_map = {
        'id_usuario': request.idUsuario,
        'id_dialogo': dialog.id,
        'tipo': PROMPT_INNOVATION_AWARD
    }

    size, page, sort = processar_parametros(size, page, sort)

    service = DialogoService(db, qdrant_client)
    return _execute_service(service.listar_historico, size, page, sort, filter_map)

@innovation_award_router.post(CHATBOT_URI_V2 + "/innovation-awards/finish-webchat-session", status_code=status.HTTP_200_OK)
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