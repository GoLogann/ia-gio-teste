from sentence_transformers import SentenceTransformer
import torch

class SentenceTransformersEmbeddingClient:
    def __init__(self):
        device = "cpu"
        self.model = SentenceTransformer("all-MiniLM-L6-v2").to(device)
        self.device = device

    def embed(self, text):
        embedding = self.model.encode(text, convert_to_tensor=True).to(self.device)
        return embedding.cpu().numpy().tolist()
