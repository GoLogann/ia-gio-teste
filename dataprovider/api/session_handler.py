import uuid
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Retorna o histórico de mensagens da sessão.
    Se a sessão não existir, cria um novo histórico de mensagens.
    """
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def get_session_history_bot(session_id: str) -> ChatMessageHistory:
    """
    Retorna o histórico de mensagens da sessão.
    Se a sessão não existir, cria um novo histórico de mensagens.
    """
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def session_exist(session_id: str) -> bool:
    """
    Verifica se a sessão existe.
    """
    return session_id in store

def end_session(session_id: str) -> None:
    """
    Finaliza a sessão com o ID fornecido.
    """
    if session_id in store:
        history = get_session_history(session_id)
        history.clear()
        del store[session_id]
    else:
        raise SessionNotFoundError(f"Sessão com ID '{session_id}' não encontrada.")


def generate_session_id() -> str:
    """
    Gera um novo UUID como ID de sessão.
    """
    return str(uuid.uuid4())


class SessionNotFoundError(Exception):
    """Exceção lançada quando uma sessão não é encontrada."""
