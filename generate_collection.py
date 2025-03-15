from qdrant_client import QdrantClient
from qdrant_client.http import models
from resources.database.config import CLIENT_QDRANT

def get_qdrant_client() -> QdrantClient:
    print(CLIENT_QDRANT)
    return QdrantClient(host='plataformagt-qdrant', port=6333)

def create_collection(client, collection_name="chunks", vector_size=384, distance_metric=models.Distance.COSINE):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=vector_size, distance=distance_metric)
    )


def delete_collection(client, collection_name="chunks"):
    client.delete_collection(collection_name=collection_name)
    print(f"Coleção '{collection_name}' apagada com sucesso!")

if __name__ == "__main__":

        c = get_qdrant_client()
        create_collection(c)
