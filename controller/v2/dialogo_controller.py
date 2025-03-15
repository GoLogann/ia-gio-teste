from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Header, UploadFile, File
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session
from typing import Any

from auth.auth import validate_jwt_token
from constantes_globais.enum.tipo_dialogo import PROMPT_ESCAVADORA, PROMPT_CRIATIVA, PROMPT_CONTESTACAO
from domain.schemas.configuracao_modelo_schema import ConfiguracaoModeloSchema
from domain.schemas.dialogo_schema import DialogoListHistory, DialogoSchema
from domain.schemas.gio_schema import GioRequestSchema, GioDescricaoSchema, GioResumoSchema, GioScrapingSchema
from repository.dialogo_repository import fetch_chat_history
from services.configuracao_service import ConfiguracaoService
from services.dialogo_service import DialogoService
from database.database import get_db
from constantes_globais.apiuri import IA_URI_V2
from database.qdrant_db import get_qdrant_client
from dataprovider.api.session_handler import end_session
from utils.helpers import processar_parametros
from dataprovider.api.authmanager import validar_e_preencher_usuario

router = APIRouter()

@router.post(IA_URI_V2 + "/perguntando/gio-enxame", status_code=status.HTTP_201_CREATED)
def perguntando_gio_enxame(
        request: Request,
        gio: GioRequestSchema,
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client),
        jwt_payload: dict = Depends(validate_jwt_token)
) -> Any:
    """
    Endpoint para criar ou atualizar um diálogo com uma pergunta de Gio Enxame.
    """
    try:
        usuario = validar_e_preencher_usuario(request, gio, jwt_payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao validar o usuário: {str(e)}"
        )
    gio.id_usuario = usuario.id
    service = DialogoService(db, qdrant_client)
    return service.perguntando_gio_enxame(gio)


@router.post(IA_URI_V2 + "/perguntando/gio-criativa", status_code=status.HTTP_201_CREATED)
def perguntando_gio_criativa(
        request: Request,
        gio: GioRequestSchema,
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client),
        jwt_payload: dict = Depends(validate_jwt_token)
) -> DialogoSchema:
    """
    Endpoint para criar ou atualizar um diálogo com uma pergunta de Gio Criativa.
    """
    try:
        usuario = validar_e_preencher_usuario(request, gio, jwt_payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao validar o usuário: {str(e)}"
        )
    gio.id_usuario = usuario.id
    service = DialogoService(db, qdrant_client)
    return _execute_service(service.perguntar_gio_criativa, gio)


@router.post(IA_URI_V2 + "/perguntando/gio-escavadora", status_code=status.HTTP_201_CREATED,
             response_model=DialogoSchema)
def perguntando_gio_escavadora(
        request: Request,
        gio: GioRequestSchema,
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client),
        jwt_payload: dict = Depends(validate_jwt_token)
) -> DialogoSchema:
    """
    Endpoint para criar ou atualizar um diálogo com uma pergunta de Gio Escavadora.
    """
    try:
        usuario = validar_e_preencher_usuario(request, gio, jwt_payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao validar o usuário: {str(e)}"
        )
    gio.id_usuario = usuario.id
    service = DialogoService(db, qdrant_client)
    return _execute_service(service.perguntar_gio_escavadora, gio)

@router.post(IA_URI_V2 + "/perguntando/gio-perplexity", status_code=status.HTTP_201_CREATED, response_model=DialogoSchema)
def perguntando_gio_perplexity(
        request: Request,
        gio: GioRequestSchema,
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client),
        jwt_payload: dict = Depends(validate_jwt_token)
) -> DialogoSchema:
    """
    Endpoint para criar ou atualizar um diálogo com uma pergunta de Gio Perplexity.
    """
    try:
        usuario = validar_e_preencher_usuario(request, gio, jwt_payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao validar o usuário: {str(e)}"
        )

    gio.id_usuario = usuario.id
    service = DialogoService(db, qdrant_client)
    return _execute_service(service.perguntando_gio_perplexity, gio)


@router.post(IA_URI_V2 + "/perguntando/gio-anthropic", status_code=status.HTTP_201_CREATED,
             response_model=DialogoSchema)
def perguntando_gio_anthropic(
        request: Request,
        gio: GioRequestSchema,
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client),
        jwt_payload: dict = Depends(validate_jwt_token)
) -> DialogoSchema:
    """
    Endpoint para criar ou atualizar um diálogo com uma pergunta de Gio Anthropic.
    """
    try:
        usuario = validar_e_preencher_usuario(request, gio, jwt_payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao validar o usuário: {str(e)}"
        )

    gio.id_usuario = usuario.id
    service = DialogoService(db, qdrant_client)
    return _execute_service(service.perguntando_gio_anthropic, gio)


@router.post(IA_URI_V2 + "/perguntando/descricao", status_code=status.HTTP_201_CREATED)
def perguntando_descricao(
        request: Request,
        gio: GioDescricaoSchema,
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client),
        jwt_payload: dict = Depends(validate_jwt_token)
) -> Any:
    """
    Endpoint para gerar uma descrição de uma tarefa através do titulo e uma breve descrição.
    """
    try:
        usuario = validar_e_preencher_usuario(request, gio, jwt_payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao validar o usuário: {str(e)}"
        )
    gio.id_usuario = usuario.id
    service = DialogoService(db, qdrant_client)
    return _execute_service(service.perguntar_descricao, gio)


@router.post(IA_URI_V2 + "/perguntando/resumo-reuniao", status_code=status.HTTP_201_CREATED)
async def perguntando_resumo(
        request: Request,
        gio: GioResumoSchema = Depends(),
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client),
        jwt_payload: dict = Depends(validate_jwt_token)
) -> Any:
    """
    Endpoint para gerar um resumo de uma reunião através de uma transcrição.
    """
    try:
        usuario = validar_e_preencher_usuario(request, gio, jwt_payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao validar o usuário: {str(e)}"
        )
    try:
        gio.id_usuario = usuario.id
        transcricao = await file.read()
        gio.transcricao = transcricao.decode('utf-8')
        service = DialogoService(db, qdrant_client)
        return _execute_service(service.gerar_resumo, gio)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro de upload de arquivo: {str(e)}"
        )


@router.post(IA_URI_V2 + "/scraping/informacoes", status_code=status.HTTP_201_CREATED)
async def perguntando_resumo(
        request: Request,
        gio: GioScrapingSchema,
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client),
        # jwt_payload: dict = Depends(validate_jwt_token)
) -> Any:
    """
    Endpoint para gerar um resumo de uma reunião através de uma transcrição.
    """
    # try:
    #     usuario = validar_e_preencher_usuario(request, gio, jwt_payload)
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"Ocorreu um erro inesperado ao validar o usuário: {str(e)}"
    #     )
    try:
        # gio.id_usuario = usuario.id
        service = DialogoService(db, qdrant_client)
        return _execute_service(service.gerar_scraping_info, gio)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro de upload de arquivo: {str(e)}"
        )


@router.post(IA_URI_V2 + "/adicionar-modelo", status_code=status.HTTP_201_CREATED)
def adicionar_modelo(
        modelo: ConfiguracaoModeloSchema,
        db: Session = Depends(get_db)
) -> Any:
    """
    Endpoint para adicionar um novo modelo de linguagem.
    """
    service = ConfiguracaoService(db)
    _execute_service(service.add_modelo_llm, modelo)
    return "modelo adicionado"


@router.delete(IA_URI_V2 + "/deletar-modelo/{id_provedor}", status_code=status.HTTP_200_OK)
def deletar_modelo(id_provedor: UUID, db: Session = Depends(get_db)) -> Any:
    """
    Endpoint para deletar um modelo completo do banco.
    Inclui a exclusão de Configuração, Provedor, ProvedorModelo e ContextoModelo.
    """
    service = ConfiguracaoService(db)
    _execute_service(service.delete_modelo_llm, id_provedor)
    return {"message": "modelo deletado com sucesso"}


@router.get(IA_URI_V2 + "/modelos", status_code=status.HTTP_200_OK)
def listar_modelos(db: Session = Depends(get_db)) -> Any:
    """
    Endpoint para listar todos os modelos e seus contextos.
    """
    service = ConfiguracaoService(db)
    modelos = service.get_todos_modelos()
    return modelos


@router.post(IA_URI_V2 + "/perguntando/contestacao", status_code=status.HTTP_200_OK)
def perguntando_gio_contestacao(
        gio: GioRequestSchema,
        request: Request,
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client),
        jwt_payload: dict = Depends(validate_jwt_token)
) -> Any:
    try:
        usuario = validar_e_preencher_usuario(request, gio, jwt_payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao validar o usuário: {str(e)}"
        )
    gio.id_usuario = usuario.id
    service = DialogoService(db, qdrant_client)
    return _execute_service(service.perguntar_gio_contestacao, gio, request)


@router.post(IA_URI_V2 + "/list-dialogo", status_code=status.HTTP_200_OK)
def listar_dialogos(
        request: DialogoListHistory,
        size: int = Query(10, ge=0),
        page: int = Query(0, ge=0),
        sort: str = Query("id DESC"),
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client),
        jwt_payload: dict = Depends(validate_jwt_token)
):
    """
    Endpoint para listar o histórico de diálogos com paginação e ordenação.
    """

    id_usuario = jwt_payload.get("sub")

    filtro = {
        'id_usuario': id_usuario,
        'id_dialogo': request.idDialogo,
        'tipo': request.tipo
    }

    size, page, sort = processar_parametros(size, page, sort)

    service = DialogoService(db, qdrant_client)
    return _execute_service(service.listar_historico, size, page, sort, filtro)


@router.post(IA_URI_V2 + "/filtro/contestacao", status_code=status.HTTP_200_OK)
def listar_dialogos(
        request: DialogoListHistory,
        size: int = Query(10, agt=0),
        page: int = Query(0, ge=0),
        sort: str = Query("id DESC"),
        db: Session = Depends(get_db),
        qdrant_client: QdrantClient = Depends(get_qdrant_client)
):
    """
    Endpoint para listar o histórico de diálogos com paginação e ordenação.
    """

    filtro = {'id_usuario': request.idUsuario,
              'id_dialogo': request.idDialogo,
              'tipo': PROMPT_CONTESTACAO}

    size, page, sort = processar_parametros(size, page, sort)

    service = DialogoService(db, qdrant_client)
    return _execute_service(service.listar_historico, size, page, sort, filtro)


@router.post(IA_URI_V2 + "/list-chat/criativa")
def listar_chat_criativa(request: DialogoListHistory, db: Session = Depends(get_db)):
    filtro = {'id_usuario': request.idUsuario,
              'id_dialogo': request.idDialogo,
              'tipo': PROMPT_CRIATIVA}

    try:
        response = fetch_chat_history(
            id_usuario=filtro['id_usuario'],
            tipo_dialogo=filtro['tipo'],
            id_dialogo=filtro['id_dialogo'],
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro durante a consulta do histórico de diálogos: {str(e)}")

    return response


@router.post(IA_URI_V2 + "/list-chat/enxame")
def listar_chat_criativa(
        request: DialogoListHistory,
        db: Session = Depends(get_db),
        jwt_payload: dict = Depends(validate_jwt_token)
):
    id_usuario = jwt_payload.get("sub")

    filtro = {
        'id_usuario': id_usuario,
        'id_dialogo': request.idDialogo,
        'tipo': 4
    }

    try:
        response = fetch_chat_history(
            id_usuario=filtro['id_usuario'],
            tipo_dialogo=filtro['tipo'],
            id_dialogo=filtro['id_dialogo'],
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro durante a consulta do histórico de diálogos: {str(e)}")

    return response


@router.post(IA_URI_V2 + "/list-chat/escavadora")
def listar_chat_criativa(request: DialogoListHistory, db: Session = Depends(get_db)):
    filtro = {'id_usuario': request.idUsuario,
              'id_dialogo': request.idDialogo,
              'tipo': PROMPT_ESCAVADORA}

    try:
        response = fetch_chat_history(
            id_usuario=filtro['id_usuario'],
            tipo_dialogo=filtro['tipo'],
            id_dialogo=filtro['id_dialogo'],
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro durante a consulta do histórico de diálogos: {str(e)}")

    return response


@router.post(IA_URI_V2 + "/finalizar-consulta-gio-criativa")
def finaliza_sessao_gio_criativa(id_usuario: str = Query(..., alias="idUsuario")):
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


@router.post(IA_URI_V2 + "/finalizar-consulta-gio-escavadora")
def finaliza_sessao_gio_escavadora(id_usuario: str = Query(..., alias="idUsuario")):
    """
    Endpoint para finalizar sessão na Gio esvadpra.
    """
    try:
        end_session(id_usuario)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

    return {"data": "Sessão finalizada"}


@router.post(IA_URI_V2 + "/finalizar-consulta-gio-perplexity")
def finaliza_sessao_gio_perplexity(id_usuario: str = Query(..., alias="idUsuario")):
    """
    Endpoint para finalizar sessão do perplexity na Gio.
    """
    try:
        end_session(id_usuario)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

    return {"data": "Sessão finalizada"}


@router.post(IA_URI_V2 + "/finalizar-consulta-gio-anthropic")
def finaliza_sessao_gio_anthropic(id_usuario: str = Query(..., alias="idUsuario")):
    """
    Endpoint para finalizar sessão do Anthropic na Gio.
    """
    try:
        end_session(id_usuario)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

    return {"data": "Sessão finalizada"}


def _execute_service(service_method, *args, **kwargs):
    """
    Função auxiliar para executar métodos do serviço com tratamento de exceções.
    """
    try:
        return service_method(*args, **kwargs)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Erro ao processar a solicitação: {str(e)}")
