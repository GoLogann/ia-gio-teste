from services.sentence_transformers import SentenceTransformersEmbeddingClient


class EmbeddingService:
    def __init__(self, embedding_client: SentenceTransformersEmbeddingClient):
        self.embedding_client = embedding_client

    def generate_embeddings(self, chunks):
        return [self.embedding_client.embed(chunk) for chunk in chunks]