import traceback
from typing import List

from pydantic import BaseModel
from qdrant_client.models import PointStruct, VectorParams, Distance
from qdrant_client import QdrantClient

from resources.database.config import CLIENT_QDRANT

class Document(BaseModel):
    text: str
    embedding: List[float]

class QueryResponse(BaseModel):
    text: str


class QdrantVectorStore:
    def __init__(self):
        self.client = QdrantClient(url=CLIENT_QDRANT)

    def save(self, collection_name: str, user_id: str, chunks: List[str], chunk_embeddings: List[List[float]]):
        """
        Salva os embeddings no Qdrant, criando uma nova coleção se necessário.

        :param collection_name: Nome da coleção no Qdrant
        :param chunks: Lista de chunks de texto
        :param chunk_embeddings: Lista de embeddings correspondentes aos chunks
        """
        points = [
            {
                "id": i,
                "vector": vector,
                "payload": {"text": chunks[i]}
            }
            for i, vector in enumerate(chunk_embeddings)
        ]

        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=len(chunk_embeddings[0]), distance=Distance.COSINE),
            )

        self.client.upsert(collection_name=collection_name, points=points)


    def get_all(self, collection_name: str) -> List[Document]:
        if not self.client.collection_exists(collection_name):
            raise ValueError(f"Collection '{collection_name}' not found.")

        scroll_result = self.client.scroll(collection_name=collection_name)

        points = scroll_result[0]

        documents = []
        for point in points:
            vector = point.vector if point.vector is not None else []
            documents.append(Document(text=point.payload["text"], embedding=vector))

        return documents