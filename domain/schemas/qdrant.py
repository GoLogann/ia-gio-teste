from pydantic import BaseModel, conlist
from qdrant_client.http import models

class CollectionData(BaseModel):
    collection_name: str
    vector_size: int = 384
    distance_metric: models.Distance = models.Distance.COSINE


class VectorData(BaseModel):
    vector_id: int
    vector: conlist(float, min_length=1)