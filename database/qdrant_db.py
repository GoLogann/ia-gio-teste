from qdrant_client import QdrantClient
from qdrant_client.http import models
from resources.database.config import CLIENT_QDRANT
import logging

logger = logging.getLogger(__name__)

def get_qdrant_client() -> QdrantClient:
    """Inicializa e retorna um cliente do Qdrant."""
    return QdrantClient(url=CLIENT_QDRANT)


def collection_exists(client: QdrantClient, collection_name: str) -> bool:
    """Verifica se uma coleção existe no Qdrant."""
    try:
        collections = client.get_collections().collections
        return any(collection.name == collection_name for collection in collections)
    except Exception as e:
        logger.error(f"Erro ao verificar existência da coleção '{collection_name}': {e}")
        return False


def create_collection(
    client: QdrantClient,
    collection_name: str = "chunks",
    vector_size: int = 384,
    distance_metric: models.Distance = models.Distance.COSINE
) -> bool:
    """Cria uma coleção no Qdrant se ela não existir."""
    try:
        if not collection_exists(client, collection_name):
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=distance_metric)
            )
            logger.info(f"Coleção '{collection_name}' criada com sucesso!")
        else:
            logger.info(f"Coleção '{collection_name}' já existe. Nenhuma ação necessária.")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar coleção '{collection_name}': {e}")
        return False


def delete_collection(client: QdrantClient, collection_name: str) -> bool:
    """Apaga uma coleção no Qdrant, se existir."""
    try:
        if collection_exists(client, collection_name):
            client.delete_collection(collection_name=collection_name)
            logger.info(f"Coleção '{collection_name}' apagada com sucesso!")
        else:
            logger.info(f"Coleção '{collection_name}' não existe. Nenhuma ação realizada.")
        return True
    except Exception as e:
        logger.error(f"Erro ao apagar coleção '{collection_name}': {e}")
        return False


def upsert_point(
    client: QdrantClient,
    collection_name: str,
    point_id: str,
    vector: list[float],
    payload: dict
) -> bool:
    """Adiciona ou atualiza um ponto na coleção."""
    try:
        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        logger.info(f"Ponto com ID '{point_id}' adicionado/atualizado na coleção '{collection_name}'.")
        return True
    except Exception as e:
        logger.error(f"Erro ao adicionar/atualizar ponto na coleção '{collection_name}': {e}")
        return False


def get_point(client: QdrantClient, collection_name: str, point_id: str) -> dict:
    """Recupera um ponto por ID na coleção."""
    try:
        response = client.retrieve(
            collection_name=collection_name,
            ids=[point_id]
        )
        if response:
            logger.info(f"Ponto com ID '{point_id}' encontrado na coleção '{collection_name}'.")
            return response[0].payload if hasattr(response[0], 'payload') else {}
        else:
            logger.info(f"Nenhum ponto encontrado com ID '{point_id}' na coleção '{collection_name}'.")
            return {}
    except Exception as e:
        logger.error(f"Erro ao recuperar ponto da coleção '{collection_name}': {e}")
        return {}


def search_points_by_field(
    client: QdrantClient,
    collection_name: str,
    field: str,
    value: str,
    limit: int = 10
) -> list[dict]:
    """Busca pontos que correspondam a um campo específico no payload."""
    try:
        filtro = models.Filter(
            must=[models.FieldCondition(
                key=field,
                match=models.MatchValue(value=value)
            )]
        )
        pontos = client.scroll(collection_name=collection_name, filter=filtro, limit=limit)
        logger.info(f"{len(pontos[0])} ponto(s) encontrado(s) na coleção '{collection_name}' para '{field}={value}'.")
        return pontos[0] if pontos else []
    except Exception as e:
        logger.error(f"Erro ao buscar pontos na coleção '{collection_name}' com '{field}={value}': {e}")
        return []


def update_payload(client: QdrantClient, collection_name: str, point_id: str, payload: dict) -> bool:
    """Atualiza apenas o payload de um ponto."""
    try:
        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=None,
                    payload=payload
                )
            ]
        )
        logger.info(f"Payload do ponto com ID '{point_id}' atualizado na coleção '{collection_name}'.")
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar payload do ponto com ID '{point_id}' na coleção '{collection_name}': {e}")
        return False


def delete_point(client: QdrantClient, collection_name: str, point_id: str) -> bool:
    """Apaga um ponto da coleção."""
    try:
        client.delete(
            collection_name=collection_name,
            points_selector=models.PointIdsList(ids=[point_id])
        )
        logger.info(f"Ponto com ID '{point_id}' removido da coleção '{collection_name}'.")
        return True
    except Exception as e:
        logger.error(f"Erro ao remover ponto com ID '{point_id}' da coleção '{collection_name}': {e}")
        return False


def delete_points_by_filter(client: QdrantClient, collection_name: str, field: str, value: str) -> bool:
    """Remove pontos que correspondam a um campo específico no payload."""
    try:
        filtro = models.Filter(
            must=[models.FieldCondition(
                key=field,
                match=models.MatchValue(value=value)
            )]
        )
        client.delete(collection_name=collection_name, points_selector=filtro)
        logger.info(f"Pontos com '{field}={value}' removidos da coleção '{collection_name}'.")
        return True
    except Exception as e:
        logger.error(f"Erro ao remover pontos por filtro na coleção '{collection_name}': {e}")
        return False


def scroll_points(client: QdrantClient, collection_name: str, limit: int = 10) -> list[dict]:
    """Lista pontos da coleção com paginação."""
    try:
        response = client.scroll(
            collection_name=collection_name,
            limit=limit
        )
        logger.info(f"Scroll realizado na coleção '{collection_name}', retornando até {limit} pontos.")
        return response[0] if response else []
    except Exception as e:
        logger.error(f"Erro ao listar pontos da coleção '{collection_name}': {e}")
        return []
